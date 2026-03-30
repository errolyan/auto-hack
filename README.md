# 🎯 autohack - 用AI赋能你的命令行

## 🛠️ 概述

autohack 将多种AI模型带到Kali命令行。这个工具帮助像你这样的操作人员直接在终端中编写命令、运行工具和维护上下文——无需桌面，无需GUI。它非常适合红队操作和蓝队防御者。autohack直接在战斗空间中提供AI能力。

## 📦 下载与安装

### 安装步骤

1. **选择你的版本**\
   找到可用的最新版本。寻找适合你操作系统的文件。
2. **下载文件**\
   点击与你的系统对应的下载链接。
3. **安装应用程序**
   - 打开你的终端。
   - 导航到你下载autohack文件的目录。
   - 按照发布说明中提供的安装说明进行操作，这些说明可能因版本而异。
4. **安装依赖**\
   安装必要的Python依赖：
   ```bash
   pip install anthropic openai google-generativeai
   ```
5. **设置环境变量**\
   根据你要使用的AI模型，设置相应的API密钥：
   ```bash
   # Claude
   export ANTHROPIC_API_KEY=your_anthropic_api_key

   # GPT
   export OPENAI_API_KEY=your_openai_api_key

   # Gemini
   export GOOGLE_API_KEY=your_google_api_key
   ```
6. **运行autohack**\
   安装后，你可以直接从命令行开始使用autohack：
   ```bash
   python claude_chat.py
   ```

## 🖥️ 系统要求

要成功运行autohack，请确保你的系统满足以下要求：

- **操作系统：** Kali Linux 2020或更高版本
- **处理器：** 双核处理器或更好
- **内存：** 至少4 GB RAM
- **磁盘空间：** 至少200 MB可用空间
- **Python：** 必须安装3.9或更高版本

确保你的环境按照这些规范设置，以获得最佳体验。

## ⚙️ 功能

autohack 配备了丰富的功能，增强你的命令行体验：

### 核心功能

- **多AI模型支持：** 集成Claude、GPT和Gemini三种AI模型，可随时切换
- **上下文感知：** 在操作过程中无缝维护上下文
- **工具自动化：** 轻松自动化重复任务
- **节省时间：** 借助AI的力量更快地完成任务
- **专注于CLI：** 为命令行爱好者和操作人员设计

### 自动化工作流

- **预定义工作流模板：** 包括侦察、Web漏洞扫描和密码破解
- **自定义工作流：** 支持用户创建和管理自定义工作流
- **变量支持：** 工作流中支持变量替换，提高灵活性

### 命令行界面改进

- **彩色输出：** 丰富的颜色和格式化选项，提升可读性
- **交互式菜单：** 友好的菜单系统，方便操作
- **命令历史记录：** 保存和浏览历史命令
- **命令自动补全：** 智能的命令、模型和工作流补全

这些功能共同作用，使执行复杂任务变得更加容易，让你可以专注于目标而不受不必要的干扰。

## 🚀 使用方法

### 基本命令

- **runlocal** **<command>** - 本地执行命令，无AI分析
- **runclaude** **<command>** - AI执行并分析命令
- **model** **<model>** - 切换AI模型（选项：claude, gpt, gemini）
- **models** - 列出可用的AI模型
- **workflows** - 列出可用的工作流
- **runworkflow** **<name>** **\<var1=value1>** - 运行带变量的工作流
- **createworkflow** **<name>** **<json>** - 创建新工作流
- **deleteworkflow** **<name>** - 删除工作流
- **menu** - 显示交互式菜单
- **quit 或 exit** - 退出autohack
- **clear** - 清除对话历史

### 示例

1. **执行命令并分析：**
   ```
   runclaude nmap -sV 192.168.1.1
   ```
2. **切换AI模型：**
   ```
   model gpt
   ```
3. **运行工作流：**
   ```
   runworkflow reconnaissance target=example.com
   ```
4. **进入交互式菜单：**
   ```
   menu
   ```

## 🙋 常见问题

### 什么是autohack？

autohack是一个命令行工具，集成了多种AI模型，直接在Kali Linux的终端中协助各种操作。

### 谁应该使用autohack？

这个工具非常适合网络安全专业人员、红队操作人员、蓝队防御者以及任何有兴趣增强命令行能力的人。

### 如果遇到问题，我该如何获得帮助？

如果你遇到问题，请查看存储库中可用的文档，或访问发布页面上链接的社区论坛以获取支持。

### 如何切换AI模型？

使用`model`命令切换不同的AI模型，例如：`model gpt`。

### 如何创建自定义工作流？

使用`createworkflow`命令创建自定义工作流，例如：

```
createworkflow myworkflow {"name": "My Workflow", "description": "自定义工作流", "steps": [{"command": "echo test", "description": "测试步骤"}], "variables": []}
```

## 📝 贡献

autohack欢迎贡献！如果你想帮助改进这个项目：

1. **分叉存储库：** 点击存储库页面右上角的"Fork"按钮。
2. **进行更改：** 创建一个新分支并进行更改。
3. **提交拉取请求：** 当你的更改准备就绪后，提交拉取请求以供审核。

通过贡献，你可以帮助让autohack对每个人都变得更好！

## 🌐 社区

加入autohack社区，与其他也在使用该工具的人联系。分享你的经验，提供提示，并向他人学习：

- **GitHub讨论**：与用户和开发人员互动。
- **社交媒体**：关注我们的Twitter和LinkedIn以获取更新。

## 💡 提示

- 通过在终端中输入`python claude_chat.py --help`来探索内置帮助功能，了解命令和选项。
- 定期检查发布页面以获取更新，以增强你使用autohack的体验。
- 使用`menu`命令进入交互式菜单，更方便地使用各种功能。
- 利用命令历史记录和自动补全功能提高操作效率。

