import { readFileSync } from "node:fs";
import { readFile, stat, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright-core";

const gemini = "https://gemini.google.com";
const responses = "model-response";
const mediaHosts = new Set(["gemini.google.com", "lh3.google.com", "lh3.googleusercontent.com"]);
const formats = ["image/png", "image/jpeg", "image/webp"];

export function imageSource(value, identified, width, height) {
  if (width < 256 || height < 256) return false;
  let url;
  try { url = new URL(value); } catch { return false; }
  if (url.protocol === "blob:") return identified && url.origin === gemini;
  if (url.protocol === "data:") return identified && /^data:image\/(png|jpeg|webp);base64,/i.test(value);
  return url.protocol === "https:" && !url.port && !url.username && !url.password &&
    mediaHosts.has(url.hostname) && (identified || /^\/(?:gg|gg-dl|rd-gg)(?:\/|$)/.test(url.pathname));
}

export function imageInstruction(prompt) {
  return "Hãy tạo và trả về một ảnh mới dựa trên mô tả dưới đây.\n\n" + prompt;
}

async function editorFor(page) {
  const editor = page.locator('rich-textarea [contenteditable="true"]:visible, .ql-editor[contenteditable="true"]:visible, [contenteditable="true"][role="textbox"]:visible').first();
  try { await editor.waitFor({state:"visible", timeout: 22000}); }
  catch { throw new Error("Không thấy ô chat. Bấm Kết nối Gemini và đăng nhập trong cửa sổ của app."); }
  return editor;
}

export async function attachReference(page, path) {
  const references = [path];
  let stage = "tìm ô tải ảnh";
  try {
    // Prefer an image picker, never an unrelated audio/video/directory picker.
    const findInput = async () => {
      const inputs = page.locator('input[type="file"]');
      const index = await inputs.evaluateAll(nodes => nodes.map((node, index) => {
        const accept = node.accept.toLowerCase();
        const image = !accept || accept === "*/*" || /image|\.png|\.jpe?g|\.webp/.test(accept);
        return {index, score: !node.disabled && !node.webkitdirectory && image ?
          (accept.includes("image") ? 20 : 10) + (node.multiple ? 5 : 0) : -1};
      }).filter(item => item.score >= 0).sort((a, b) => b.score - a.score)[0]?.index ?? -1);
      return index < 0 ? null : inputs.nth(index);
    };
    let input = await findInput();
    if (!input) {
      let chooser;
      const opened = value => { chooser = value; };
      // Subscribe before clicking: some versions open the OS chooser directly,
      // others create a file input only after the local-upload menu item is used.
      page.on("filechooser", opened);
      try {
        stage = "mở nút đính kèm của Gemini";
        const named = page.getByRole("button", {name:/upload|attach|add (?:files?|photos?|images?)|open.*file|tải.*(?:tệp|ảnh)|(?:thêm|đính kèm).*(?:tệp|ảnh)/i}).filter({visible:true});
        const icons = page.locator('mat-icon, .google-symbols, .material-symbols-outlined, .material-icons').filter({hasText:/^(add|attach_file|upload_file|add_circle|add_2)$/});
        const iconButton = page.getByRole("button").filter({has:icons}).filter({visible:true});
        const opener = page.locator("button.upload-card-button, button[data-test-id=upload-button]").or(named).or(iconButton).filter({visible:true}).first();
        await opener.click({timeout:10000});
        input = await findInput();
        if (!input && !chooser) {
          stage = "chọn tải ảnh từ máy tính";
          const label = /^(upload files?|upload from (?:computer|device)|from computer|tải (?:tệp|ảnh)(?: lên)?|tải lên từ (?:máy tính|thiết bị)|(?:chọn|tải) (?:tệp|ảnh) từ máy tính)$/i;
          const item = page.locator("[data-test-id='local-images-files-uploader-button']").or(page.getByRole("menuitem", {name:label}).or(page.getByRole("button", {name:label}))).filter({visible:true}).first();
          await item.click({timeout:10000});
        }
        const deadline = Date.now() + 10000;
        while (!input && !chooser && Date.now() < deadline) {
          input = await findInput();
          if (!input && !chooser) await page.waitForTimeout(100);
        }
        if (chooser) {
          const selected = chooser;
          input = {setInputFiles:(files, options) => selected.setFiles(files, options)};
        }
      } finally {
        page.off("filechooser", opened);
      }
    }
    if (!input) throw new Error("Không tìm thấy ô tải ảnh của Gemini; chưa gửi prompt.");
    const before = await page.locator("img").evaluateAll(nodes => nodes.map(node => node.currentSrc || node.src));
    const previewSelector = 'uploader-file-preview, file-preview, .file-preview, .attachment-preview';
    const previousPreviews = await page.locator(previewSelector).filter({visible:true}).count();
    const pending = new Set();
    let lastUpload = 0;
    let uploadFailed = false;
    const started = request => {
      if (/upload|content-push/i.test(request.url()) && !["GET", "OPTIONS"].includes(request.method())) {
        pending.add(request); lastUpload = Date.now();
      }
    };
    const finished = request => { if (pending.delete(request)) lastUpload = Date.now(); };
    const failed = request => { if (pending.has(request)) uploadFailed = true; finished(request); };
    const response = response => { if (pending.has(response.request()) && response.status() >= 400) uploadFailed = true; };
    page.on("request", started);
    page.on("response", response);
    page.on("requestfinished", finished);
    page.on("requestfailed", failed);
    try {
      stage = "chuyển file ảnh tham chiếu vào Gemini";
      await input.setInputFiles(references, {timeout:20000});
      stage = "chờ ảnh tham chiếu tải xong";
      lastUpload = Date.now();
      // Accept real thumbnails or visible file names too. Gemini component names
      // vary; hidden progress elements must not keep a completed upload blocked.
      await page.waitForFunction(({before, names, previewSelector, previousPreviews}) => {
        const visible = node => Boolean(node.getClientRects().length) && getComputedStyle(node).visibility !== "hidden";
        const progress = [...document.querySelectorAll('[role="progressbar"], .upload-progress')].some(visible);
        const previews = [...document.querySelectorAll(previewSelector)].filter(visible).length;
        const thumbnails = [...document.images].filter(image =>
          visible(image) && image.complete && image.naturalWidth > 0 && !before.includes(image.currentSrc || image.src)).length;
        const text = document.body.innerText;
        const named = names.every(name => text.includes(name));
        return !progress && (previews >= previousPreviews + names.length || thumbnails >= names.length || named);
      }, {before, names:references.map(file => file.split(/[\\/]/).pop()), previewSelector, previousPreviews}, {timeout:60000});
      const deadline = Date.now() + 60000;
      while (pending.size || (lastUpload && Date.now() - lastUpload < 750)) {
        if (Date.now() > deadline) throw new Error("Ảnh tham chiếu chưa tải xong; chưa gửi prompt.");
        await page.waitForTimeout(150);
      }
      if (uploadFailed) throw new Error("Gemini từ chối tải ảnh tham chiếu; chưa gửi prompt.");
    } finally {
      page.off("request", started);
      page.off("response", response);
      page.off("requestfinished", finished);
      page.off("requestfailed", failed);
    }
  } catch (error) {
    if (error.name !== "TimeoutError") throw error;
    throw new Error(`Gemini hết thời gian ở bước ${stage}. App chưa gửi prompt.`);
  }
}

async function submit(page, editor, prompt) {
  const count = await page.locator(responses).count();
  await editor.fill(prompt);
  const send = page.getByRole("button", {name:/^(send( message| prompt)?|gửi( tin nhắn| lời nhắc)?)$/i})
    .or(page.locator("button.send-button")).first();
  await send.click({timeout:12000});
  return page.locator(responses).nth(count);
}

async function waitForText(page, answer) {
  await answer.waitFor({state:"visible", timeout:75000});
  const stop = page.getByRole("button", {name:/^(stop|dừng|ngừng)(\b|\s)/i}).first();
  const end = Date.now()+45000;
  let last = "", changed = Date.now();
  while (Date.now() < end) {
    const message = answer.locator("message-content, .markdown").first();
    const text = (await (await message.count() ? message : answer).innerText({timeout:4000})).trim();
    if (text !== last) { last = text; changed = Date.now(); }
    if (text && !(await stop.isVisible()) && Date.now() - changed >= 2500) return text;
    await new Promise(resolve => setTimeout(resolve, 400));
  }
  throw new Error("Gemini chưa viết xong prompt.");
}

async function waitForImage(response) {
  await response.waitFor({state:"visible",timeout:90000});
  const end = Date.now() + 120000;
  while (Date.now() < end) {
    const elements = response.locator("img");
    const images = await elements.evaluateAll(nodes => nodes.map((image, index) => ({
      index,
      url: image.currentSrc,
      identified: Boolean(image.closest("generated-image, generated-image-container, single-image, image-generation")),
      width: image.naturalWidth, height: image.naturalHeight,
    })));
    const image = images.find(item => imageSource(item.url, item.identified, item.width, item.height));
    if (image) return {...image, element: elements.nth(image.index)};
    await new Promise(resolve => setTimeout(resolve, 600));
  }
  throw new Error("Gemini chưa trả ảnh mới cho lượt này. Có thể yêu cầu chỉ nhận phản hồi văn bản.");
}

async function downloadImage(context, page, image) {
  let bytes, type;
  if (image.url.startsWith("blob:") || image.url.startsWith("data:")) {
    const result = await page.evaluate(async url => {
      const response = await fetch(url, {signal: AbortSignal.timeout(15000)});
      const type = response.headers.get("content-type")?.split(";")[0];
      const blob = await response.blob();
      if (blob.size > 24_000_000) throw Error("Ảnh quá lớn.");
      return await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve({type, data: reader.result.split(",")[1]});
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
    }, image.url);
    bytes = Buffer.from(result.data, "base64");
    type = result.type;
  } else {
    const request = await context.request.get(image.url, {
      maxRedirects:0, timeout:20000, headers:{referer:gemini+"/"},
    });
    try {
      if (!request.ok()) throw new Error("Gemini hiện ảnh nhưng Studio chưa tải được file.");
      type = request.headers()["content-type"]?.split(";")[0];
      bytes = await request.body();
    } finally {
      await request.dispose();
    }
  }
  if (!formats.includes(type) || !bytes.length || bytes.length > 24_000_000) {
    throw new Error("File ảnh không hợp lệ hoặc vượt quá 24 MB.");
  }
  return bytes;
}

async function downloadFromGemini(page, answer, image) {
  await image.element.hover({timeout:5000});
  const buttonName = /download|tải xuống|tải ảnh/i;
  const figure = image.element.locator("xpath=ancestor::*[self::generated-image or self::generated-image-container or self::single-image or self::image-generation][1]");
  const downloadControl = scope => scope.getByRole("button", {name:buttonName})
    .or(scope.getByRole("link", {name:buttonName})).filter({visible:true});
  const local = downloadControl(figure);
  const control = await local.count() ? local : downloadControl(answer);
  if (await control.count() !== 1) throw new Error("Không xác định được nút tải ảnh của Gemini.");

  const pending = page.waitForEvent("download", {timeout:20000}).catch(() => null);
  try {
    await control.click({timeout:5000});
  } catch {
    // A click can trigger a download before the browser reports a navigation error.
  }
  const download = await pending;
  if (!download) throw new Error("Gemini chưa gửi file ảnh tải xuống.");
  let timeout;
  try {
    const path = await Promise.race([
      download.path(),
      new Promise((_, reject) => {
        timeout = setTimeout(() => reject(new Error("Gemini tải ảnh quá lâu.")), 15000);
      }),
    ]);
    if ((await stat(path)).size > 24_000_000) throw new Error("Ảnh vượt quá 24 MB.");
    const bytes = await readFile(path);
    const png = bytes.subarray(0, 8).toString("hex") === "89504e470d0a1a0a";
    const jpeg = bytes.subarray(0, 3).toString("hex") === "ffd8ff";
    const webp = bytes.toString("ascii", 0, 4) === "RIFF" && bytes.toString("ascii", 8, 12) === "WEBP";
    if (!png && !jpeg && !webp) throw new Error("File tải xuống không phải ảnh được hỗ trợ.");
    return bytes;
  } finally {
    clearTimeout(timeout);
    await download.cancel().catch(() => {});
    await download.delete().catch(() => {});
  }
}

async function copyImagePixels(image) {
  const data = await image.element.evaluate((element, url) => {
    const {naturalWidth:width, naturalHeight:height} = element;
    if (element.currentSrc !== url || width < 256 || height < 256 || width * height > 25_000_000) {
      throw new Error("Ảnh kết quả không còn sẵn sàng.");
    }
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    canvas.getContext("2d").drawImage(element, 0, 0);
    return canvas.toDataURL("image/png").split(",", 2)[1];
  }, image.url, {timeout:5000});
  if (!data || data.length > 32_000_000) throw new Error("Ảnh vượt quá 24 MB.");
  return Buffer.from(data, "base64");
}

async function saveResult(context, page, answer, image, output) {
  const bytes = await downloadFromGemini(page, answer, image).catch(() =>
    downloadImage(context, page, image)).catch(() =>
    copyImagePixels(image)).catch(() => {
    throw new Error("Gemini đã hiện ảnh nhưng app chưa tải được file ảnh. Hãy thử lại.");
  });
  await writeFile(output, bytes, {flag:"wx"});
}

async function run(port, request) {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:" + port, {timeout:12000});
  try {
    if (request.action === "shutdown") {
      const session = await browser.newBrowserCDPSession();
      await session.send("Browser.close").catch(() => {});
      return {};
    }
    const context = browser.contexts()[0];
    if (!context) throw new Error("Không tìm thấy hồ sơ Chrome của app.");
    const page = context.pages().find(item => item.url() === "about:blank");
    if (!page) throw new Error("Không tìm thấy tab xử lý nền. Hãy thoát app và mở lại.");
    try {
      await page.goto(gemini + "/app", {waitUntil:"domcontentloaded", timeout:30000});
      if (new URL(page.url()).origin !== gemini) throw new Error("Hãy hoàn tất đăng nhập bằng nút Đăng nhập Gemini.");
      const cookies = await context.cookies(gemini + "/app");
      if (!cookies.some(({name}) => name === "__Secure-1PSID")) {
        throw new Error("Chưa thấy phiên Google đã đăng nhập trong hồ sơ Gemini của app.");
      }
      const editor = await editorFor(page);
      if (request.action === "verify") return {signedIn:true};
      if (request.action === "prompt") {
        const instruction = "Viết lại mô tả dưới đây thành một prompt tạo ảnh chi tiết. Giữ nguyên ngôn ngữ, " +
          "chủ thể và ý định chính. Mô tả rõ bố cục và ánh sáng nếu phù hợp. Chỉ trả prompt.\n\n" + request.prompt;
        return {text: await waitForText(page, await submit(page, editor, instruction))};
      }
      if (request.action !== "image") throw new Error("Yêu cầu Gemini không hợp lệ.");
      let instruction = imageInstruction(request.prompt);
      if (request.reference) {
        try {
          await attachReference(page, request.reference);
        } catch (error) {
          if (request.diagnoseUpload) {
            throw new Error("Hãy xem cửa sổ Gemini để kiểm tra ảnh xem trước hoặc thông báo lỗi. App chưa gửi prompt.");
          }
          throw error;
        }
        if (request.diagnoseUpload) return {attached:true};
        instruction = "Hãy tạo một ảnh mới dựa trên ảnh tham chiếu đính kèm. Giữ các đặc điểm nhận diện của chủ thể trong ảnh, trừ những phần mà mô tả yêu cầu thay đổi. Trả về ảnh theo yêu cầu sau.\n\n" + request.prompt;
      }
      const answer = await submit(page, editor, instruction);
      const image = await waitForImage(answer);
      await saveResult(context, page, answer, image, request.output);
      return {saved:true};
    } finally {
      if (!request.diagnoseUpload) {
        await page.goto("about:blank", {timeout:5000, waitUntil:"commit"}).catch(() => {});
      }
    }
  } finally {
    await browser.close().catch(() => {});
  }
}

async function main() {
  try {
    const {port, request} = JSON.parse(readFileSync(0, "utf8"));
    if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error("Chrome chưa sẵn sàng.");
    process.stdout.write(JSON.stringify({result:await run(port, request)}));
  } catch (error) {
    const message = error.name === "TimeoutError" ? "Hết thời gian chờ Gemini." : error.message;
    process.stdout.write(JSON.stringify({error:message.split("\n")[0].slice(0,300)}));
    process.exitCode = 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await main();
