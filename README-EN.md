<br />

<div align="center">
  <a href="https://github.com/IdeaSphere-team/IdeaSphere/">
    <img src="/templates/static/img/logo-white.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">IdeaSphere</h3>

<p align="center">
  A forum software focusing on simplicity, practicality and easy configuration, built with Python3.
</p>
<p align="center">
  主打简单实用易于配置的论坛程序，基于 Python3 完成
</p>

[![GitHub forks](https://img.shields.io/github/forks/IdeaSphere-team/IdeaSphere.svg?style=for-the-badge)](https://github.comIdeaSphere-team/IdeaSphere/network)
[![Stars](https://img.shields.io/github/stars/IdeaSphere-team/IdeaSphere.svg?style=for-the-badge)](https://github.com/IdeaSphere-team/IdeaSphere/stargazers)  
[![GitHub license](https://img.shields.io/github/license/IdeaSphere-team/IdeaSphere.svg?style=for-the-badge)](https://github.com/IdeaSphere-team/IdeaSphere/blob/main/LICENSE)
[![Python version](https://img.shields.io/badge/python-3.11+-blue?style=for-the-badge&logo=python)](https://www.python.org/downloads/release/python-3110/)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-blueviolet?style=for-the-badge)](https://pypi.org/project/Flask/)
[![Discord](https://img.shields.io/discord/1349304044723765258?style=for-the-badge&logo=discord)](https://discord.gg/eyn9GC88XP)

<p align="center">
  <a href="https://github.com/IdeaSphere-team/IdeaSphere/blob/main/README.md">简体中文</a> | English
</p>

</div>


## 📖 Project introduction

`IdeaSphere` is a simple and useful forum program based on Python 3.11 and Flask framework. It is easy to configure and suitable for quickly setting up a lightweight forum system.

# 🌟 Core Features

- **Simple and Easy to Use**: Clean interface, practical functions, and easy to get started.
- **Easy to Configure**: Most configurations can be completed through the `config.yml` file.
- **Lightweight**: Developed with the Flask framework, ensuring high performance.
- **Modular Design**: Clear code structure for easy expansion and maintenance.

## 🌟 Realization function

| Task Overview | Current Status | Implementation Version |
|---|---|---|
| **⌨️ Login** | ✅ | v0.1.0 |
| **⌨️ Registration** | ✅ | v0.1.0 |
| **⌨️ Post Creation** | ✅ | v0.1.0 |
| **🖼 Super Administrator** | ✅ | v0.1.0 |
| **🖼 Moderator Administrator** | ✅ | v0.1.0 |
| **👤 Like Functionality** | ✅ | v0.1.0 |
| **🧱 Reporting System** | ✅ | v0.1.0 |
| **📦 Online Users** | ✅ | v0.1.0 |
| **⭐ Post Replies** | ✅ | v0.1.0 |
| **🔬 Search** | ✅ | v0.1.5 |
| **👤 Site Statistics** | ✅ | v0.1.5 |
| **🚀 Admin Panel** | ✅ | v0.2.0 |
| **📦 Emoji Support** | ✅ | v0.2.0 |
| **🔬 Post Deletion** | ✅ | v0.2.5 |
| **👤 Permission Groups** | ✅ | v0.2.5 |
| **👤 Full Permission Group Implementation** | 🚧 | |
| **⭐ ICenter (For details, see [here](https://github.com/IdeaSphere-team/IdeaSphere/issues/5))** | 🚧 | |
| **⭐ Content Replies** | 🚧 | |
| **⭐ Content Reactions** | 🚧 | |
| **🎈 Rich Text Editor** | 🚧 | |
| **🎈 Post Sections** | 🚧 | |
| **👤 Post Creation Time and Like Count Sorting** | 🚧 | |
| **👤 Reply Time and Like Count Sorting** | 🚧 | |
| **📦 Private Messaging System** | ⏳ | |
| **📦 User Customization Settings** | ⏳ | |
| **📦 User Profile Page** | ⏳ | |
| **🔐 Email Registration and Password Reset** | ⏳ | |
| **🔌 Templates** | ⏳ | |
| **🔌 Plugins** | ⏳ | |
| **🔐 Data Security** | ⏳ | |
| **🔐 SEO Optimization** | ⏳ | |

Here is the translation of the legend for your reference:

- ✅: Task completed. Great job! 🎉
- 🚧: Task in progress. We're working hard! 💪
- ⏳: Task upcoming. Something exciting is coming soon! 🌠

# 🛠️ Installation Guide

## 1. Environment Requirements

- **Python Version**: 3.11 or higher
- **Operating System**: Windows, Linux, macOS

## 2. Download the Project

```bash
git clone https://github.com/IdeaSphere-team/IdeaSphere.git  
cd IdeaSphere
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Parameters

Modify the `config.yml` file to suit your environment:

(It will be generated automatically on the first program launch)

```bash
port: 5000  # Program runtime port
```

## 5. Start the Program

```bash
python app.py
```

Default access address: `http://localhost:5000`

# 🎯 Usage Instructions

## 1. Installation Wizard

On your first visit to the forum, you'll automatically enter the installation wizard page (`/install`). Follow the prompts to complete the installation.

## 2. User Registration and Login

Users can register for a new account via the `/register` page. After registration, use the `/login` page to log in.

## 3. Posting and Commenting

After logging in, users can access the `/post` page to create new posts. On the post details page (`/view_post`), users can post comments.

## 4. Admin Backend

Administrators can manage users, posts, and comments via the `/admin` page.

# ⬆️ Contributing

We welcome your participation in IdeaSphere's development. Follow these steps to submit your contributions:

1. Fork this repository to your GitHub account
2. Clone your account's repository to your local machine
   `git clone https://github.com/  your_username/IdeaSphere.git`
3. Make changes, build, and test the documentation locally. Once verified, push to your repository
4. Return to this repository, click Pull requests -> New pull request to initiate a PR

# 📞 Contact Us

If you have any questions or suggestions, feel free to reach out to us through the following methods:

- Submit [GitHub Issues](https://github.com/IdeaSphere-team/IdeaSphere/issues/new/choose  )
- QQ Group: [![QQ](https://img.shields.io/badge/QQ%E4%BA%A4%E6%B5%81%E7%BE%A4-1036347298-20B2AA?style=for-the-badge  )](http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=0S7iEPBCDpSWgvzARFqxM_zyIlnQ2-km&authKey=AiX0JpNVU8d%2BIjMocMxVhE0OcxbdOaQAt1wnnekYg%2BYQ0GZfOy3KXuSFTBZ2pDD2&noverify=0&group_code=1036347298  )
- Discord: [![Discord](https://img.shields.io/discord/1349304044723765258?style=for-the-badge&logo=discord  )](https://discord.gg/eyn9GC88XP  )

## 🤝 Contributor

[![Contrib](https://contrib.rocks/image?repo=IdeaSphere-team/IdeaSphere)](https://github.com/IdeaSphere-team/IdeaSphere/graphs/contributors)

## ⭐ Star history chart

[![Stargazers over time](https://starchart.cc/IdeaSphere-team/IdeaSphere.svg?variant=adaptive)](https://starchart.cc/IdeaSphere-team/IdeaSphere)

## 😊 Disclaimer

> [!NOTE]
> This project is intended for learning and reference purposes only. When using it, please ensure compliance with relevant laws, regulations, and website service terms.

## 🎫 License

> [!NOTE]
> This project is licensed under the `MIT License`. For more details, please refer to the `LICENSE` file.

```
MIT License

Copyright (c) 2025 IdeaSphere-team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
