# GOST 可视化管理面板

Web 界面管理 GOST 转发规则，替代脚本的添加/修改/删除操作。

## 功能

- 查看所有转发规则
- 新增 / 编辑 / 删除规则
- 重启 GOST 服务
- 支持所有协议类型（不加密、TLS/WS/WSS、代理、均衡负载、CDN 等）

## 安装

### 方式一：通过 gost.sh

```bash
./gost.sh
# 选择 12 - 安装/管理 Web 可视面板
```

### 方式二：手动安装

```bash
cd panel
chmod +x install_panel.sh
sudo ./install_panel.sh
```

## 访问

- 地址：`http://服务器IP:5000`
- 默认账号：`admin` / `admin`

面板监听 0.0.0.0:5000，可通过服务器 IP 直接访问。**请务必修改默认密码。**

## 修改账号密码

编辑 systemd 服务文件：

```bash
nano /usr/lib/systemd/system/gost-panel.service
```

添加或修改：

```
Environment=GOST_PANEL_USER=你的用户名
Environment=GOST_PANEL_PASS=你的密码
```

然后执行：

```bash
systemctl daemon-reload
systemctl restart gost-panel
```

## 管理命令

```bash
systemctl start gost-panel   # 启动
systemctl stop gost-panel    # 停止
systemctl restart gost-panel # 重启
systemctl status gost-panel  # 状态
```

## 依赖

- 已安装 GOST（通过 gost.sh 安装）
- Python 3.6+
- Flask

## 安全说明

- 面板需 root 权限读写 `/etc/gost/` 并执行 `systemctl`
- 监听 0.0.0.0:5000，可通过服务器 IP 访问
- **请务必修改默认密码**，避免未授权访问
