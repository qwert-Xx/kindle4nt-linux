# SPDX-License-Identifier: GPL-2.0-or-later
import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('builder', pathlib.Path(__file__).with_name('build.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class Inputs(unittest.TestCase):
    def test_relative_and_corruption(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td)
            (p / 'data').write_bytes(b'input')
            manifest = {'inputs': {'config': {'path': 'data', 'sha256': b.digest(p / 'data')}}}
            (p / 'inputs.json').write_text(json.dumps(manifest))
            self.assertEqual(b.inputs(p / 'inputs.json')['inputs']['config']['resolved'], str(p / 'data'))
            (p / 'data').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                b.inputs(p / 'inputs.json')

    def test_hashed_precompiled_inputs_need_no_private_profile(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td)
            (p / 'payload').write_bytes(b'precompiled input')
            manifest = {'inputs': {name: {'path': 'payload', 'sha256': b.digest(p / 'payload')}
                                   for name in ('ram_root', 'barebox')}}
            recipe = p / 'inputs.json'
            recipe.write_text(json.dumps(manifest))
            loaded = b.inputs(recipe)
            for name in manifest['inputs']:
                self.assertEqual(loaded['inputs'][name]['resolved'], str(p / 'payload'))
            (p / 'payload').write_bytes(b'corrupted input')
            with self.assertRaisesRegex(ValueError, 'input hash mismatch'):
                b.inputs(recipe)

    def test_missing(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / 'inputs.json'
            p.write_text('{"inputs":{"config":{"path":"missing","sha256":"0"}}}')
            with self.assertRaises(ValueError):
                b.inputs(p)


class BuildModes(unittest.TestCase):
    """Exercise main's mode dispatch with host compilation replaced by fixtures."""
    RELEASE = '6.6.157-k4-production'
    BUILTINS = ('IMX2_WDT', 'DEVTMPFS', 'DEVTMPFS_MOUNT', 'EXT4_FS', 'MMC',
                'MMC_BLOCK', 'MMC_SDHCI', 'MMC_SDHCI_PLTFM', 'MMC_SDHCI_ESDHC_IMX')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.source = self.root / 'linux'
        self.source.mkdir()
        (self.source / 'Makefile').write_text('# fixture Linux source\n')
        self.target = 'nxp/imx/imx50-kindle-k4.dtb'
        dts = self.source / 'arch/arm/boot/dts' / pathlib.Path(self.target).with_suffix('.dts')
        dts.parent.mkdir(parents=True)
        dts.write_text('/dts-v1/; / {};\n')
        self.out = self.root / 'out'
        # Minimal ARM zImage/ELF headers with the release fields read by the assembler.
        header = bytearray(40)
        header[36:40] = (0x016f2818).to_bytes(4, 'little')
        self.kernel = bytes(header) + b'Linux version ' + self.RELEASE.encode() + b' fixture\0'
        elf = bytearray(52)
        elf[:4] = b'\x7fELF'
        elf[18:20] = (40).to_bytes(2, 'little')
        self.module = bytes(elf) + b'vermagic=' + self.RELEASE.encode() + b' SMP\0'
        self.dtb = b'fixture dtb'
        self.lock = {'zImage': self.sha(self.kernel), 'dtb': self.sha(self.dtb),
                     'modules': {'kernel/fixture.ko': self.sha(self.module)},
                     'toolchain': {'compiler': 'release gcc', 'linker': 'release ld'}}
        self.commands = []

    @staticmethod
    def sha(data):
        return b.hashlib.sha256(data).hexdigest()

    def fake_run(self, command, **kwargs):
        self.commands.append(command)
        if 'k4_defconfig' in command:
            (self.out / '.config').write_text(''.join('CONFIG_' + key + '=y\n' for key in self.BUILTINS))
        elif command[0] == 'bash':
            with (self.out / '.config').open('a') as config:
                config.write(pathlib.Path(command[-1]).read_text())
        elif 'zImage' in command:
            for path, data in ((self.out / 'arch/arm/boot/zImage', self.kernel),
                               (self.out / 'arch/arm/boot/dts' / self.target, self.dtb)):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        elif 'modules_install' in command:
            module = self.out / 'root-modules/lib/modules' / self.RELEASE / 'kernel/fixture.ko'
            module.parent.mkdir(parents=True)
            module.write_bytes(self.module)
        else:
            self.assertIn('olddefconfig', command)
        return b.subprocess.CompletedProcess(command, 0)

    def invoke(self, *arguments):
        original_read = pathlib.Path.read_text
        release_lock = pathlib.Path(b.__file__).parent / 'alpine/kernel.lock.json'

        def read_text(path, *args, **kwargs):
            return json.dumps(self.lock) if path == release_lock else original_read(path, *args, **kwargs)

        with mock.patch.object(b, 'SOURCE', self.source), \
                mock.patch.object(sys, 'argv', ['build.py', '--out', str(self.out), *arguments]), \
                mock.patch.object(b.subprocess, 'run', side_effect=self.fake_run), \
                mock.patch.object(b, 'toolchain', return_value='ordinary gcc') as compiler, \
                mock.patch.object(pathlib.Path, 'read_text', read_text), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            b.main()
        return json.loads((self.out / 'build-report.json').read_text()), compiler, stdout.getvalue()

    def test_default_source_accepts_individual_diagnostic_override(self):
        fragment = self.root / 'diagnostic.config'
        fragment.write_text('CONFIG_ATH6KL_DEBUG=y\n')
        report, compiler, _ = self.invoke('--config', str(fragment))
        self.assertEqual(report['mode'], 'source')
        self.assertFalse(report['release_verified'])
        compiler.assert_called_once_with('arm-linux-gnueabihf-', None)
        self.assertTrue(any('zImage' in command for command in self.commands))
        self.assertIn('CONFIG_ATH6KL_DEBUG=y\n', (self.out / '.config').read_text())
        self.assertNotIn('CONFIG_K4_DIAGNOSTICS=y', (self.out / '.config').read_text())
        self.assertEqual(len(report['modules']), 1)

    def test_prebuilt_uses_hashed_inputs_without_compilation(self):
        payloads = {'zImage': self.kernel, 'dtb': self.dtb}
        modules = self.root / 'modules.tar.gz'
        with tarfile.open(modules, 'w:gz') as archive:
            member = tarfile.TarInfo('lib/modules/' + self.RELEASE + '/kernel/fixture.ko')
            member.size = len(self.module)
            archive.addfile(member, io.BytesIO(self.module))
        payloads['modules'] = modules.read_bytes()
        manifest = {'inputs': {}}
        for name, data in payloads.items():
            path = self.root / (name + '.input')
            path.write_bytes(data)
            manifest['inputs'][name] = {'path': path.name, 'sha256': self.sha(data)}
        recipe = self.root / 'prebuilt.json'
        recipe.write_text(json.dumps(manifest))
        report, compiler, _ = self.invoke('--mode', 'prebuilt', '--inputs', str(recipe))
        self.assertEqual(report['mode'], 'prebuilt')
        self.assertEqual(report['kernel_release'], self.RELEASE)
        self.assertEqual(report['artifacts']['zImage'], self.sha(self.kernel))
        self.assertEqual(len(report['modules']), 1)
        self.assertFalse(report['release_verified'])
        self.assertEqual(self.commands, [])
        compiler.assert_not_called()

    def test_reproduce_explicitly_checks_toolchain_and_artifact_lock(self):
        report, compiler, stdout = self.invoke('--mode', 'reproduce')
        compiler.assert_called_once_with('arm-linux-gnueabihf-', self.lock['toolchain'])
        self.assertTrue(report['release_verified'])
        self.assertIn('VERIFY_RELEASE_OK ' + self.RELEASE + ' modules=1', stdout)

    def test_release_mismatch_is_rejected_only_when_requested(self):
        self.lock['zImage'] = '0' * 64
        report, compiler, _ = self.invoke('--mode', 'source')
        self.assertFalse(report['release_verified'])
        compiler.assert_called_once_with('arm-linux-gnueabihf-', None)
        for arguments in (('--mode', 'reproduce'), ('--verify-release',)):
            with self.subTest(arguments=arguments), self.assertRaisesRegex(ValueError, 'release hash mismatch'):
                self.invoke(*arguments)


if __name__ == '__main__':
    unittest.main()
