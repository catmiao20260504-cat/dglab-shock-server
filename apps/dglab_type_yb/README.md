# 拼音打字训练 × DG-Lab 电击惩罚版

实时拼音打字练习工具。每输入一个错误字符，立即触发电击惩罚并自动删除错误输入，强迫你保持准确率。词库从本地文本文件加载，支持自定义。

## 截图

<!-- 可放截图 -->

## 功能

- 实时逐字符检测：输错即触发电击，不等你按回车
- 错误字符自动删除，必须重新输入正确拼音才能继续
- 词库从本地 `source/` 目录读取（英文拼音 + 对应中文）
- 游戏结束显示总错误次数与准确率
- 右侧控制面板：
  - A / B 通道强度滑块（0~200）
  - 电击持续时间设置（默认 1500ms）
  - 6 种内置波形预设 + 自定义 HEX 导入
  - 手动测试电击按钮
  - 设备实时强度显示
  - 紧急停止

## 文件结构

此应用需要额外的词库文件，完整目录结构如下：

```
apps/pinyin-trainer/
├── index.html
├── README.md
└── source/
    ├── english.txt     ← 每行一个拼音（如 jiangnan）
    └── chinese.txt     ← 每行对应的中文（如 江南）
```

`english.txt` 与 `chinese.txt` 行数必须一一对应。

**示例：**

```
# english.txt        # chinese.txt
jiangnan             江南
beijing              北京
zhongguo             中国
```

## 使用方法

1. 在 `apps/pinyin-trainer/` 下创建 `source/` 文件夹
2. 准备 `english.txt` 和 `chinese.txt` 词库文件
3. 启动服务端：`python server/dglab_server.py`
4. 郊狼 App 扫码绑定
5. **必须通过本地服务器打开**（不能直接双击 HTML），例如：
   ```bash
   # 在 apps/pinyin-trainer/ 目录下执行
   python -m http.server 8080
   # 浏览器访问 http://localhost:8080
   ```
   或使用 VS Code 的 Live Server 插件
6. 右侧面板填写 DG-Lab 服务端地址，点击「Connect / Test」
7. 状态显示已绑定后开始打字

> ⚠️ 必须用本地服务器（http://）打开，直接双击（file://）会因浏览器安全限制无法读取词库文件。

## 电击触发条件

| 触发事件 | A 通道强度 | B 通道强度 | 持续时间 |
|----------|-----------|-----------|----------|
| 输入错误字符 | 面板可调（默认 20） | 面板可调（默认 10） | 面板可调（默认 1500ms） |

错误触发后输入框自动清空，需重新输入当前词的正确拼音。

## 依赖

- `dglab_server.py` v1.0+
- 接入方式：`POST /cmd` + `GET /status`（HTTP API）
- 需要本地 HTTP 服务器（用于加载词库文件）
- 词库文件：`source/english.txt` + `source/chinese.txt`
