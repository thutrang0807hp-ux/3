async function generateInGemini(prompt, ratio, refine) {
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  const visible = node => node.getClientRects().length > 0;
  const editor = () => Array.from(document.querySelectorAll(
    'rich-textarea [contenteditable="true"], .ql-editor[contenteditable="true"], [contenteditable="true"][role="textbox"]'
  )).find(visible);
  const findButton = (selector, label) => Array.from(document.querySelectorAll(selector))
    .find(button => visible(button) && !button.disabled && button.getAttribute("aria-disabled") !== "true" &&
      ((selector.includes("button.send-button") && button.classList.contains("send-button")) ||
       label.test(button.getAttribute("aria-label") || button.title || "")));
  const responseSelector = "model-response, .model-response-text";
  const assistantMessages = () => Array.from(document.querySelectorAll(responseSelector))
    .filter(node => !node.parentElement?.closest(responseSelector));
  const isResponding = () => findButton(
    "button[aria-label], button[title]",
    /^(stop|dừng|ngừng)(\b|\s)/i
  );
  const generatedImages = message => [...message.querySelectorAll("img")].filter(image =>
    image.complete && image.naturalWidth >= 256 && image.naturalHeight >= 256 &&
    (image.closest("generated-image, single-image, image-generation, generated-image-container") ||
     /^blob:|^data:image\//.test(image.currentSrc) ||
     /^https:\/\/[^/]+\.googleusercontent\.com\//.test(image.currentSrc))
  );

  async function until(read, limit) {
    const end = Date.now() + limit;
    do {
      const result = read();
      if (result) return result;
      await wait(250);
    } while (Date.now() < end);
  }

  async function readImage(image) {
    let file;
    try {
      const response = await fetch(image.currentSrc, {signal: AbortSignal.timeout(15000)});
      if (response.ok) file = await response.blob();
    } catch {
      // Some Gemini image hosts allow rendering but restrict direct fetches.
    }
    if (!file?.type.startsWith("image/")) {
      const canvas = document.createElement("canvas");
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;
      canvas.getContext("2d").drawImage(image, 0, 0);
      file = await new Promise(resolve => canvas.toBlob(resolve, "image/png"));
    }
    if (!file || !["image/png", "image/jpeg", "image/webp"].includes(file.type) || file.size > 8_000_000) {
      throw new Error("Không thể chuyển ảnh này về Studio.");
    }
    return await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve({image: reader.result.split(",")[1], mime: file.type});
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  let revised = refine ? "" : prompt;
  try {
    async function sendMessage(message) {
      const input = await until(editor, 20000);
      if (!input) throw new Error("Không thấy ô chat Gemini. Hãy kiểm tra bạn đã đăng nhập Gemini Chat trên Chrome.");
      const previousMessages = new Set(assistantMessages());
      input.focus();
      if (!document.execCommand("insertText", false, message)) {
        input.textContent = message;
        input.dispatchEvent(new InputEvent("input", {bubbles: true, inputType: "insertText", data: message}));
      }
      const send = await until(() => findButton(
        "button.send-button, button[aria-label], button[title]", /^(send( message| prompt)?|gửi( tin nhắn| lời nhắc)?)$/i
      ), 8000);
      if (!send) throw new Error("Gemini đã đổi giao diện hoặc chưa cho phép gửi prompt.");
      send.click();
      return () => assistantMessages().filter(node => !previousMessages.has(node)).at(-1);
    }

    if (refine) {
      const latest = await sendMessage(
        "Viết lại ý tưởng sau thành đúng một prompt tạo ảnh. Giữ ngôn ngữ gốc. Chỉ trả prompt giữa [PROMPT] và [/PROMPT]. Không tạo ảnh ở bước này.\n\n" + prompt
      );
      let lastText = "";
      let lastChange = Date.now();
      revised = await until(() => {
        const node = latest();
        const content = (node?.querySelector("message-content, .markdown")?.innerText || node?.innerText || "").trim();
        if (content !== lastText) {
          lastText = content;
          lastChange = Date.now();
        }
        if (!content || isResponding() || !editor()) return;
        const marked = content.match(/\[PROMPT\]\s*([\s\S]+?)\s*\[\/PROMPT\]/i)?.[1]?.trim();
        if (marked) return marked;
        if (Date.now() - lastChange < 3000) return;
        return content.replace(/^\s*\[PROMPT\]\s*|\s*\[\/PROMPT\]\s*$/gi, "").trim();
      }, 45000);
      if (!revised) throw new Error("Gemini chưa trả văn bản sau 45 giây. Hãy thử gửi lại.");
    }
    const latest = await sendMessage("Hãy tạo một ảnh theo đúng prompt này. Tỷ lệ ảnh: " + ratio + "\n\n" + revised);
    const output = await until(() => {
      const node = latest();
      return node && generatedImages(node).at(-1);
    }, 135000);
    if (!output) throw new Error("Gemini chưa trả ảnh sau khoảng 2 phút. Bạn có thể bấm Tạo lại ảnh để thử với prompt đã chỉnh.");
    try {
      return {prompt: revised, ...await readImage(output)};
    } catch (error) {
      const url = new URL(output.currentSrc);
      if (url.protocol === "https:" && url.hostname.endsWith(".googleusercontent.com")) {
        return {prompt: revised, imageUrl: url.href};
      }
      throw error;
    }
  } catch (error) {
    return {prompt: revised, error: error.message || "Không đọc được kết quả từ Gemini."};
  }
}
