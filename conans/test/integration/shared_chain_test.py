import os
import shutil
import unittest

from nose.plugins.attrib import attr

from conans.test.utils.cpp_test_files import cpp_hello_conan_files
from conans.test.utils.tools import TestClient, TestServer
from conans.util.files import rmdir


@attr("slow")
class SharedChainTest(unittest.TestCase):

    def setUp(self):
        self.servers = {"default": TestServer()}

    def _export_upload(self, name, version=None, deps=None):
        conan = TestClient(servers=self.servers, users={"default": [("lasote", "mypass")]})
        dll_export = conan.default_compiler_visual_studio
        files = cpp_hello_conan_files(name, version, deps, static=False, dll_export=dll_export)
        conan.save(files)

        conan.run("create . lasote/stable")
        conan.run("upload * --all --confirm")
        conan.run("remove * -f")
        rmdir(conan.current_folder)
        shutil.rmtree(conan.cache.store, ignore_errors=True)

    def uploaded_chain_test(self):
        self._export_upload("Hello0", "0.1")
        self._export_upload("Hello1", "0.1", ["Hello0/0.1@lasote/stable"])

        client = TestClient(servers=self.servers, users={"default": [("lasote", "mypass")]})
        files = cpp_hello_conan_files("Hello2", "0.1", ["Hello1/0.1@lasote/stable"], static=True)
        client.save(files)

        client.run("install .")
        client.run("build .")
        command = os.sep.join([".", "bin", "say_hello"])
        client.run_command(command)
        self.assertEqual(['Hello Hello2', 'Hello Hello1', 'Hello Hello0'],
                         str(client.out).splitlines()[-3:])
