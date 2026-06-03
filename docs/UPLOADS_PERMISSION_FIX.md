# uploads 目录权限问题修复说明

## 1. 问题现象

- 会议室照片上传失败；
- 企业诉求/约见/预约等附件上传失败；
- 后端日志出现 `Permission denied`；
- `uploads` 目录属主为 `root`，而后端进程以普通用户（如 `esc` 或开发账号）运行。

## 2. 检查命令

```bash
ls -ld uploads
ls -ld uploads/attachments
whoami
```

若 `uploads` 显示 `root root`，且当前用户不是 root，则无法写入。

## 3. 修复命令（开发环境）

当前开发用户为登录用户时：

```bash
cd /app/Enterprise-Service-Center   # 或你的项目根目录
sudo chown -R $(whoami):$(whoami) uploads
chmod -R 755 uploads
```

若后端由指定用户运行（如 systemd 的 `esc`）：

```bash
sudo chown -R esc:esc /opt/enterprise-service-center/uploads
chmod -R 750 /opt/enterprise-service-center/uploads
```

## 4. 验证命令

```bash
touch uploads/test.txt
rm uploads/test.txt
```

若使用 systemd 用户 `esc`：

```bash
sudo -u esc touch /opt/enterprise-service-center/uploads/test.txt
sudo -u esc rm -f /opt/enterprise-Service-center/uploads/test.txt
```

验证通过后再在页面上传附件或会议室照片。

## 5. 后端错误提示

上传接口在磁盘写入失败且为权限错误时，会返回明确提示：

> 文件上传失败：上传目录无写权限，请检查 uploads 目录权限

请在前端查看接口返回的 `message`，不要仅看「系统异常」。

## 6. 配置说明

`.env` 中建议：

```ini
UPLOAD_DIR=/opt/enterprise-service-center/uploads
```

使用绝对路径，且该目录对运行用户可写。

## 7. 注意事项

- 不建议长期 `chmod 777`，仅用于临时排查；
- 生产环境按 [DEPLOY_KYLIN_V10.md](./DEPLOY_KYLIN_V10.md) 使用专用运行用户并正确授权；
- 迁移服务器时需同时迁移 `uploads` 与数据库。
