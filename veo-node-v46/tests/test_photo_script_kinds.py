"""Text-only format admission and compatibility; no model requests."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from fastapi import HTTPException

ROOT=Path(__file__).parents[1]/'local_engine'
package=types.ModuleType('_script_kind_test');package.__path__=[str(ROOT)];sys.modules[package.__name__]=package
ledger=types.ModuleType(package.__name__+'.request_ledger');ledger.NO_RESULT=object();sys.modules[ledger.__name__]=ledger
spec=importlib.util.spec_from_file_location(package.__name__+'.script_library',ROOT/'script_library.py')
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)

class ScriptKinds(unittest.TestCase):
    def body(self,**kwargs):return dict(action='write',idea='Bàn chải cán xanh',product_name='Bàn chải',target_seconds=30,**kwargs)

    def test_legacy_receipt_instruction_unchanged(self):
        self.assertEqual(lib.validate_input(self.body()),lib.WRITE)

    def test_formats_change_direction_without_changing_input_or_output_contract(self):
        prompts=[]
        for kind in lib.SCRIPT_KINDS:
            body=self.body(script_kind=kind,verified_facts='Cán xanh, đầu nhỏ')
            original=dict(body);prompts.append(lib.validate_input(body))
            result=lib.validate_result(body,{'body':'Giới thiệu bàn chải.\n\nBạn xem kỹ phần đầu nhỏ nhé.'})
            self.assertEqual(result['body'],'Giới thiệu bàn chải.\n\nBạn xem kỹ phần đầu nhỏ nhé.')
            self.assertEqual(original,body)
        self.assertEqual(len(set(prompts)),len(lib.SCRIPT_KINDS))

    def test_unknown_or_malformed_kind_and_facts_rejected(self):
        for kind in ['invented',{},[],None]:
            with self.assertRaises(HTTPException) as exc:lib.validate_input(self.body(script_kind=kind))
            self.assertEqual(exc.exception.status_code,400)
        for facts in [[],None,'x'*4001]:
            with self.assertRaises(HTTPException):lib.validate_input(self.body(verified_facts=facts))

if __name__=='__main__':unittest.main()
