<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 从自己的输入生成维护配方

以下示例在仓库根执行，沿用[构建指南](BUILD.md)的 PRIVATE 和 OUT。先按[用户态配方](../userspace/README.md)生成 `OUT/userspace/bin/` 和 `busybox.links`。先按[私有输入提取指南](FIRMWARE-EXTRACTION.md)准备固件、公开监管数据库和自己的配置/密钥。PRIVATE 下准备 `firmware/`、`wpa_supplicant.conf`、`authorized_keys`、Dropbear 格式的 `dropbear-hostkey`；Alpine 可另提供 OpenSSH 格式的 `ssh_host_ecdsa_key`。

Dropbear 格式的主机密钥可在可信任的主机上用 `dropbearkey -t ecdsa -s 256 -f "$PRIVATE/dropbear-hostkey"` 生成，或从自己的维护系统备份。它与 OpenSSH 私钥格式不同。维护内嵌根以只读方式挂载，因此使用预置密钥。

下面的 Python 只生成 JSON 文件，不复制私有内容进仓库。内嵌 ext3 大小为 48 MiB，可按固件大小调大；UUID 与当前 bootstrap 的固定维护根 UUID 对应。

```sh
export PRIVATE OUT
python3 - <<'PY'
import os, sys, pathlib, json, hashlib
sys.path.insert(0, 'project')
import rootfs_sources
private = pathlib.Path(os.environ['PRIVATE']).resolve()
out = pathlib.Path(os.environ['OUT']).resolve()
userspace = out / 'userspace'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
entries = {}
def directory(n, mode=0o755):
    entries.setdefault(n, dict(name=n, kind='dir', mode=mode))
def file(n, p, mode=0o644):
    p = p.resolve()
    for parent in reversed(pathlib.PurePosixPath(n).parents):
        if str(parent) != '.': directory(str(parent))
    entries[n] = dict(name=n, kind='file', mode=mode, source=str(p), sha256=sha(p))
def link(n, target):
    for parent in reversed(pathlib.PurePosixPath(n).parents):
        if str(parent) != '.': directory(str(parent))
    entries[n] = dict(name=n, kind='link', mode=0o777, target=target)
for n in ('bin','sbin','dev','proc','sys','run','tmp','root','etc/dropbear','lib/modules'):
    directory(n, 0o1777 if n == 'tmp' else 0o755)
for n, p in rootfs_sources.files('common','busybox/maintenance').items():
    if n == 'bin/k4-modalias-coldplug': continue
    if p.is_symlink(): link(n, p.readlink().as_posix())
    else: file(n, p, p.stat().st_mode & 0o777)
for n in ('busybox','busybox-modutils','dropbear','dropbearkey','wpa_supplicant','wpa_cli','iw','k4-epd-update'):
    file('bin/' + n, userspace / 'bin' / n, 0o755)
for p in sorted((private/'firmware').rglob('*')):
    n = 'lib/firmware/' + p.relative_to(private/'firmware').as_posix()
    if p.is_symlink(): link(n, p.readlink().as_posix())
    elif p.is_dir(): directory(n)
    else: file(n, p)
file('etc/wpa_supplicant.conf', private/'wpa_supplicant.conf', 0o600)
file('etc/dropbear/k4-hostkey', private/'dropbear-hostkey', 0o600)
file('root/.ssh/authorized_keys', private/'authorized_keys', 0o600)
entries['root/.ssh']['mode'] = 0o700
link('etc/resolv.conf', '/run/resolv.conf')
for n in ('depmod','insmod','lsmod','modprobe','rmmod'):
    link('sbin/'+n, '/bin/busybox-modutils')
inner = dict(entries=list(entries.values()), image_bytes=48*1024*1024,
             uuid='8a25ce4d-0367-4a11-b617-d3846be75b46',
             busybox_links=dict(path=str(userspace/'busybox.links'), sha256=sha(userspace/'busybox.links')))
(private/'filesystem.json').write_text(json.dumps(inner, indent=2)+'\n')
entries = {}
for n in ('bin','dev','proc','sys','run','newroot'): directory(n)
for n in ('init','bin/k4-root-select','bin/k4-bootmark'):
    source = rootfs_sources.files('common','busybox/ram')[n]
    file(n, source, source.stat().st_mode & 0o777)
file('bin/busybox', userspace/'bin/busybox', 0o755)
# Early builtin drivers can request firmware before switch_root.
for p in sorted((private/'firmware').rglob('*')):
    n = 'lib/firmware/' + p.relative_to(private/'firmware').as_posix()
    if p.is_symlink(): link(n, p.readlink().as_posix())
    elif p.is_dir(): directory(n)
    else: file(n, p)
entries['dev/console'] = dict(name='dev/console', kind='char', mode=0o600, major=5, minor=1)
# The builder replaces this placeholder with the structured filesystem image.
file('rootfs.ext3', userspace/'bin/busybox')
outer = dict(entries=list(entries.values()), filesystem_recipe='filesystem.json',
             filesystem_recipe_sha256=sha(private/'filesystem.json'), private_inputs=True,
             automatic_diagnostics=False)
(private/'ram-recipe.json').write_text(json.dumps(outer, indent=2)+'\n')
inputs = dict(kernel_profile='production', release='6.6.157-k4-production',
              inputs=dict(ram_recipe=dict(path='ram-recipe.json',sha256=sha(private/'ram-recipe.json'))),
              alpine=dict(cache='alpine-cache',firmware_dir='firmware',wifi_config='wpa_supplicant.conf',
                          authorized_keys='authorized_keys',tools_dir=str(userspace/'bin')))
if (private/'ssh_host_ecdsa_key').is_file(): inputs['alpine']['ssh_host_key']='ssh_host_ecdsa_key'
(private/'inputs.json').write_text(json.dumps(inputs, indent=2)+'\n')
print('Created filesystem.json, ram-recipe.json, inputs.json')
PY
make -C project images INPUTS="$PRIVATE/inputs.json" OUT="$OUT/images"
```

修改 private 文件或清单后重新生成 JSON，更新对应 SHA。模块在实际 images 构建时加入。这个示例定义默认维护服务。
