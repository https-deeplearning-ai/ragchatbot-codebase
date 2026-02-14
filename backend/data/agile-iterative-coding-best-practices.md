# 文章来源

URL: https://baoyu.io/blog/agile-iterative-coding-best-practices

---

[宝玉的分享](https://baoyu.io/)[博客](https://baoyu.io/blog)[翻译](https://baoyu.io/translations)Menu
[](https://baoyu.io/translations)
Published on 2025-06-10
# Vibe Coding 的最佳实践仍然是 Agile 的版本迭代模式，而不是一次性完成一个庞大的无法运行和维护的半成品
![](https://baoyu.io/uploads/2025-06-10/1749573867345.png)
不知道你看到图 1 的 3 种模式有何感想，我只想说现在你用 AI 写代码，千万不要用第 1 和第 3 种模式，只能采用第 2 种模式！  
  
Vibe Coding 的最佳实践仍然是 Agile 的版本迭代模式，而不是一次性完成一个庞大的无法运行和维护的半成品，像图中第三种先做个不伦不类的东西出来，想优化成真正的产品，是不太现实，即使对于专业程序员来说也会相当有挑战，否则程序员们也不会那么热衷于“推翻重写”！  
  
举个例子，比如你要做一个 ERP 系统，你把完整需求一次性发给 Claude Code，也很专业的要它拆分成模块，再让它按照模块一个个去开发（像图2那样），但这样做出来的东西也基本上是不可控的，做出来的东西基本上无法满足需求的甚至无法运行的。因为无论是 AI 还是人类，都无法掌控这么多模块的协作，更何况还要保障每一个模块自身的稳定性。
![](https://baoyu.io/uploads/2025-06-10/1749573885391.png)
那么更好的做法是什么呢？  
  
还是要像图 1 中 Agile 的做法那样——每次做一个完整的能稳定运行的版本出来。  
  
举例来说，你要做一个 ERP 系统，分成若干版本来迭代，每一个版本都是可以独立稳定运行的，举例来说（仅供参考）：  
- v0.1: 一个可以运行的 Nextjs/TanStack 程序，有欢迎页面，可以跳转  
- v0.1: 实现 users 相关数据库访问功能，在 mysql 中创建 users 表，实现 users 表的读写功能，添加读写功能的测试代码  
- v0.2: 实现用户注册的网页，连接 users 相关数据库方法，能写入注册用户信息到数据库  
- v0.3: 实现用户登录、注销的网页功能  
- v0.4: 实现简单的 dashboard 页面  
- v0.5: 实现 products 相关数据库访问功能，写功能代码和测试  
- v0.6: 实现 products 在 dashboard 的管理页面，能显示列表  
- v0.7: 实现 products 的添加、编辑和删除功能  
- ...  
  
这里就不一一列举，核心还是每一个版本功能是完整的，可以独立运行的，测试稳定后再下一个模块。  
  
这样你基本可以保证你做出来的是可以掌控的，而不是一次性做出来一个几乎无法维护的庞大半成品。
* * *
[](https://baoyu.io/translations)
Built by [宝玉](https://twitter.com/dotey). [ RSS](https://baoyu.io/feed.xml) . 本站原创内容，独家授权赛博禅心公众号发布。
Toggle theme
