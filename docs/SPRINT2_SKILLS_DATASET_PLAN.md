# Sprint 2 执行方案：技能库与数据集（Yong Hin）

> **给 Claude Code 的执行说明。** 请从头到尾读完这份文件再动手。按 Phase 顺序做，每个 Phase 完成后跑它的「验收」检查并单独 commit。遇到「⚠️ 需要确认」的地方，如果 Yong Hin 在线就先问他；不在线就按写好的**默认做法**继续，并在最后的总结里列出来。

- 负责人：Ng Yong Hin（AI / NLP Engineer）
- 仓库：`C:\FYP Repo\Group10_ProjectA`，从 `dev` 分支开工
- Sprint：Sprint 2（Week 9–10）
- 相关需求：FR-02（技能库）、FR-03（职位模板）、FR-04（JD 技能提取）、FR-14（AI 评估，Sprint 4 用）
- 方案日期：2026-09-29

---

## 0. 背景：现在做到哪了

| 项目 | 现状 | 问题 |
|---|---|---|
| `schema.sql` 里的 `skills_library` | 32 个技能（v1） | 太少，没有网络安全技能 |
| `database/seed_skills_library_v2.sql` | 新增 69 个 → 合计 **101** 个（9/29 21:10 改过，可能还没 commit） | 文件头写的是「130 skills」，实际只有 101；alias 和 v1 冲突（见下） |
| `database/seed_job_role_skills.sql` | 6 个职位 × 79 条对应 | 只用了 v1 的 32 个技能，Cybersecurity Analyst 拿通用技能顶着 |
| `data/generate_synthetic_data.py` | 5000 个学生，seed 42，已合并进 `dev` | `load_schema_skills()` 只读 `schema.sql`，**一用 v2 的新技能就会报错退出**；ROLES/PROJECTS/CERTIFICATIONS 只用了 32 个技能 |
| JD 职位描述数据集 | **还没有** | POC 要求 5–10 个 IT 职位的真实 JD；Sprint 4 的 L1 vs L2 评估也要用 |
| `backend/routers/jobs.py` 技能排序 | 已经改成 `CASE jrs.importance`（看起来已修） | 只需确认，不用再改 |

### v2 技能库里已发现的 alias 冲突（必须修）

NLP 做关键词匹配时，一个词只能指向一个技能。现在这些词会指向两个地方：

| 文本里出现 | 现在被当成 | 但它本身也是独立技能 |
|---|---|---|
| MySQL、SQLite | SQL 的 alias | `MySQL`、`SQLite` |
| Bash、Shell scripting | Linux 的 alias | `Bash`（Shell scripting 同时是 Bash 和 Linux 的 alias） |
| AWS、Azure、GCP | Cloud Computing 的 alias | `AWS`、`Azure`、`GCP` |
| Critical thinking | Problem Solving 的 alias | `Critical Thinking` |
| Presentation skills | Communication 的 alias | `Presentation Skills` |

还有一些**容易误判的短 alias**：`CV`（Computer Vision，但 JD 里 CV 多半是「简历」）、`IR`、`BA`、`PM`、`TF`、`VA`、`np`、`pd`、`Crypto`、`R`（单字母）。另外 `Agile`、`Scrum`、`Kanban` 被放成 Project Management 的 alias，`GitHub Actions`、`Jenkins` 被放成 CI/CD 的 alias，这些在 JD 里常常是独立要求。

---

## 1. 目标与范围

### 这个 Sprint 要交付

1. **技能库 v2 定稿**：120–150 个技能，每个有 category、aliases、description；没有 alias 冲突；有单一数据源（CSV），SQL seed 由脚本生成。
2. **职位–技能对应更新**：6 个职位全部用上新技能，Cybersecurity Analyst 有真正的安全技能。
3. **合成学生数据重新生成**：生成器改为读新的技能库，ROLES/PROJECTS/CERTIFICATIONS 用上新技能，重新输出。
4. **JD 数据集**：采集格式、清洗和导入工具，加上一批真实 JD（目标见 Phase 4），以及一小份人工标注的 gold set，供 Sprint 4 评估用。
5. **测试和文档**：自动检查脚本、README 更新、报告「Dataset description」章节的草稿。

### 不在这个 Sprint 做

- NLP 提取器 `nlp/extractor.py` 和匹配器 `nlp/matcher.py`（另一份任务，Phase 5 做完后再开始）
- `assessments.py` 的加权评分
- Aaron 的 `recommendations_library` 内容（只需要保证他能用新 skill_id，见「协作注意」）

---

## 2. 规则（Claude Code 必须遵守）

1. **不要改 `database/schema.sql`**，它归 Carl 管。所有技能库变动都放在 seed 文件里。v1 里有问题的 alias 用 `UPDATE` 在 v2 seed 里修。
2. **不要改名或删除 v1 的 32 个技能**：`skill_name` 被合成数据、`job_role_skills` 和 Aaron 的推荐库引用。要调整只改 aliases 或 description。
3. **不要碰** `backend/.env`、`frontend/`、`recommendation/`、`backend/routers/`（除了 Phase 0 的只读检查）。
4. 所有 SQL seed 都要**可以重复执行**（`ON CONFLICT ... DO UPDATE`），出错时整个 transaction 回滚，技能名拼错时要报错，不能静默跳过。
5. 真实采集来的 JD 原文放 `data/raw/`（已在 `.gitignore`），**不要 commit 原始爬取文件**。可以 commit 清洗后、去掉公司敏感信息的数据集。
6. 不写自动爬虫去抓 LinkedIn / JobStreet / Indeed 等网站（违反服务条款）。JD 来源见 Phase 4。
7. 每个 Phase 一个 commit，commit message 用 `feat:` / `fix:` / `docs:` / `test:` 前缀。**不要 push 到 `dev` 或 `main`**，只 push feature 分支，然后开 PR 到 `dev`（有 `gh` 就用 `gh pr create`，没有就告诉 Yong Hin 去网页上开）。
8. Windows 环境：命令用 PowerShell 或 `cmd` 能跑的写法；路径有空格（`C:\FYP Repo\...`），要加引号。

---

## 3. 执行步骤

### Phase 0 — 开工检查（约 10 分钟）

```powershell
cd "C:\FYP Repo\Group10_ProjectA"
git status
git fetch origin
git checkout dev
git pull origin dev
```

- 如果 `database/seed_skills_library_v2.sql` 显示为未 commit 的修改：**先不要丢弃**。新建分支后把它带过去：
  ```powershell
  git checkout -b feature/skills-library-v2
  git add database/seed_skills_library_v2.sql
  git commit -m "wip: skills library v2 draft (101 skills)"
  ```
- 确认本机 PostgreSQL 17 能连：`psql -U postgres -d seagas_db -c "SELECT COUNT(*) FROM skills_library;"`（密码从 `backend/.env` 的 `DATABASE_URL` 读，**不要打印到输出里**）。
- 确认 `jobs.py` 的 `GET /api/jobs/roles/{role_id}/skills` 已经按 required → preferred → bonus 排序（`CASE jrs.importance`）。已修好就在最后的总结里写「已确认」，不用改。

**验收：** 在 `feature/skills-library-v2` 分支上，工作区干净，数据库可连。

---

### Phase 1 — 技能库单一数据源 + 修冲突 + 扩充到 120–150

#### 1.1 建立单一数据源

新建 `data/skills/skills_library.csv`，这是**唯一需要人手编辑的技能清单**。列：

| 列 | 说明 |
|---|---|
| `skill_name` | 规范名，唯一，和 DB 一致 |
| `category` | 只能是 `Technical` / `AI_Digital` / `Analytical` / `Soft`（schema 的 CHECK 约束） |
| `subcategory` | 例如 `Programming Language`、`Web Framework`、`Database`、`DevOps`、`Data & BI`、`Security Tool`、`Security Practice`、`Cloud`、`ML/AI`、`Analytical`、`Soft`。**只给 NLP 和报告用，不进 DB** |
| `aliases` | 用 `|` 分隔。会写进 DB 的 `aliases TEXT[]` |
| `ambiguous_aliases` | 用 `|` 分隔。容易误判的写法（`CV`、`R`、`IR`、`BA`、`PM`、`TF`…），**不进 DB**，NLP 以后只在大小写完全一致且有上下文时才用 |
| `description` | 一句英文说明 |
| `source` | `v1` 或 `v2`，方便追踪 |

先把 schema.sql 里 32 个 v1 技能和 v2 seed 里 69 个技能导进这份 CSV（写一个一次性脚本解析 SQL，不要手抄）。

#### 1.2 修 alias 冲突

规则：**一个 alias（不分大小写）只能属于一个技能，而且不能和任何 `skill_name` 相同。**

按下面处理（v1 的技能只改 aliases，不改名）：

| 技能 | 改法 |
|---|---|
| SQL | 去掉 `MySQL`、`SQLite`（它们是独立技能）；保留 `Structured Query Language`，`PostgreSQL` 另建独立技能或保留为 SQL alias（默认：新建 `PostgreSQL` 技能） |
| Linux | 去掉 `Bash`、`Shell scripting`；保留 `Ubuntu`，加 `Linux administration`、`Unix` |
| Cloud Computing | 去掉 `AWS`、`Azure`、`GCP`；保留 `Cloud platforms`、`Cloud infrastructure` |
| Problem Solving | 去掉 `Critical thinking` |
| Communication | 去掉 `Presentation skills` |
| Project Management | 去掉 `Agile`、`Scrum`、`Kanban`、`Sprint planning`，另建 `Agile / Scrum` 技能 |
| CI/CD | 去掉 `GitHub Actions`、`Jenkins` 作为 alias（默认：保留为 CI/CD 的 alias 也行，但**不能**同时是 Git 的 alias；Git 的 alias `GitHub`、`GitLab` 保留） |
| Computer Vision | `CV` 移到 `ambiguous_aliases` |
| 其他短 alias | `IR`、`BA`、`PM`、`TF`、`VA`、`np`、`pd`、`Crypto`、`K8`、`MSF` 移到 `ambiguous_aliases`；`R` 的 aliases 保留 `R programming`、`R language`，另在 ambiguous 里标 `R` |

#### 1.3 扩充到 120–150 个

目前 101 个，再加约 25–40 个。**优先加 JD 里常见、而现在缺的技能**。建议清单（按需取舍，最后以 Phase 4 的 JD 频率分析为准）：

- **Web / 软件工程**：TypeScript、HTML、CSS、REST API、GraphQL、Object-Oriented Programming、Data Structures & Algorithms、Unit Testing、Microservices、Agile / Scrum、UI/UX Design、Figma
- **数据**：PostgreSQL、Data Cleaning、ETL、Data Warehousing、Looker、Google Analytics、Jupyter
- **云 / DevOps**：Serverless、Monitoring & Observability（Prometheus / Grafana 作为 alias）、Networking（TCP/IP、DNS 作为 alias）、Identity & Access Management
- **安全**：OWASP Top 10、Security Operations (SOC)、Threat Intelligence、Security Frameworks（NIST、ISO 27001 作为 alias）、Malware Analysis、Log Analysis
- **AI**：Prompt Engineering、Data Ethics / Responsible AI
- **Soft / Analytical**：Stakeholder Communication（注意别和 Interpersonal Skills 冲突）、Decision Making、Customer Focus

⚠️ **需要确认（category）**：v2 把 Cybersecurity、Network Security、Cryptography、Ethical Hacking、Digital Forensics、Incident Response、Vulnerability Assessment 放在 `AI_Digital`。`assessments` 表按 category 算 `score_ai_digital`，这样网络安全学生的「AI/数字」分会虚高。
**默认做法：** 把这些安全技能改成 `Technical`（subcategory = `Security Practice`）。改之前在总结里提醒 Yong Hin 跟 Carl 确认 category 和 7 个维度分数怎么对应。

#### 1.4 由 CSV 生成 SQL seed

新建 `data/skills/build_skills_seed.py`：

- 读 `skills_library.csv`，先跑 1.5 的检查，不通过就退出（非 0 exit code）。
- 输出 `database/seed_skills_library_v2.sql`（覆盖原文件），内容：
  - `BEGIN;` … `COMMIT;`
  - `INSERT ... ON CONFLICT (skill_name) DO UPDATE SET category = EXCLUDED.category, aliases = EXCLUDED.aliases, description = EXCLUDED.description;`（这样 v1 技能的 alias 修正也会生效）
  - 文件头写明：自动生成、不要手改、技能总数、生成时间、运行方法
  - 最后跑一个按 category 统计的 `SELECT`
- 同时输出 `nlp/resources/skills_taxonomy.json`（包含 subcategory 和 ambiguous_aliases），给之后的 NLP 模块用。

#### 1.5 自动检查

新建 `tests/test_skills_library.py`（pytest），检查：

- `skill_name` 唯一（不分大小写）
- category 只有 4 个合法值
- 任何 alias 不和其他技能的 alias 或 `skill_name` 重复（不分大小写，去掉首尾空格）
- `skills_library.csv` 里包含 v1 的全部 32 个技能名，拼写完全一致
- 技能总数在 120–150 之间
- 每个技能都有 description；`skill_name` 不超过 100 个字符（DB 限制）

**验收：**
```powershell
python data/skills/build_skills_seed.py
pytest tests/test_skills_library.py -q
psql -U postgres -d seagas_db -f database/seed_skills_library_v2.sql
psql -U postgres -d seagas_db -f database/seed_skills_library_v2.sql   # 第二次也要成功，数量不变
psql -U postgres -d seagas_db -c "SELECT category, COUNT(*) FROM skills_library GROUP BY 1;"
```
Commit：`feat: skills library v2 with single CSV source, alias conflict fixes (N skills)`

---

### Phase 2 — 更新职位–技能对应（`seed_job_role_skills.sql`）

- 保留现有结构（temp table + 按 `role_code`、`skill_name` 匹配 + 技能名拼错就回滚）。
- 每个职位大约 **8–10 个 required、6–10 个 preferred、4–8 个 bonus**。
- 重点补 **Cybersecurity Analyst**：required 放 Network Security、Linux、Networking、SIEM、Incident Response、Vulnerability Assessment 这类；Cloud Computing / AWS 降为 preferred。
- Cloud Engineer 加 Kubernetes、Terraform、CI/CD、Networking、IAM；Web Developer 加 TypeScript、HTML、CSS、REST API；Data Analyst 加 Data Cleaning、Pandas；Data Scientist 加 Scikit-learn、Pandas、Feature Engineering、Model Evaluation；Software Developer 加 OOP、Data Structures & Algorithms、Unit Testing、REST API。
- 需要旧的 required 技能被降级或删除时：先删除该职位不再需要的旧对应（`DELETE ... WHERE role_id = ... AND skill_id NOT IN (新清单)`），然后 upsert。
- 在文件头注释里写清楚：Phase 4 做完 JD 频率分析后会再按数据调一次。

⚠️ **需要确认（加职位）**：POC 建议的职位还有 Business Analyst、DevOps Engineer、AI/ML Engineer。**默认做法：** 这个 Sprint 不加新职位（`job_roles` 是 schema.sql 里的 seed，归 Carl），只在总结里提出建议。

**验收：** seed 跑两次都成功；
```sql
SELECT jr.role_name, jrs.importance, COUNT(*)
FROM job_role_skills jrs JOIN job_roles jr USING (role_id)
GROUP BY 1,2 ORDER BY 1,2;
```
6 个职位每个都有三种 importance；Cybersecurity Analyst 的 required 里至少 4 个是安全类技能。
然后打开 Swagger 调一次 `GET /api/jobs/roles/{role_id}/skills`，确认返回的顺序是 required → preferred → bonus。
Commit：`feat: extend job_role_skills to skills library v2`

---

### Phase 3 — 合成学生数据生成器更新

改 `data/generate_synthetic_data.py`：

1. **技能校验改读 CSV**：`load_schema_skills()` 改成读 `data/skills/skills_library.csv`（保留 fallback：CSV 不存在时再读 schema.sql）。
2. **ROLES 和 `job_role_skills` 对齐**：最好直接从 `seed_job_role_skills.sql` 的清单派生（required → `core`，preferred + bonus → `secondary`），避免两边手动维护出现不一致。做不到就至少加一个检查：ROLES 里的 core 必须等于该职位的 required 集合。
3. **PROJECTS / CERTIFICATIONS 用上新技能**：网络安全加 CompTIA Security+、CEH、Cisco CCNA；云加 AWS Solutions Architect Associate、Azure Fundamentals (AZ-900)、CKA；数据加 Google Data Analytics、Microsoft PL-300。项目的 `skills_used` 也要用新技能。
4. **默认数量**：`argparse` 默认值是 500，README 写 5000，两边统一。⚠️ **需要确认** —— **默认做法：** 默认值改成 5000（跟已合并的数据一致），README 写清楚用 `--n 500` 生成小的演示数据集。
5. **保持确定性**：同一个 seed 必须生成相同的 UUID 和数据。
6. 重新生成 `data/output/`，更新 `summary_stats.txt`。

⚠️ **注意**：生成器改动后 UUID 和分布都会变。本机数据库要先跑 `data/delete_synthetic_data.sql` 再导入新的 seed。

**验收：**
```powershell
cd data
python generate_synthetic_data.py
cd ..
psql -U postgres -d seagas_db -f data/delete_synthetic_data.sql
psql -U postgres -d seagas_db -f data/output/seed_synthetic_students.sql
```
- 导入成功；`student_skills` 里至少有 60% 的技能库技能被使用过。
- strong / average / weak 三类的核心技能覆盖率仍然明显分层（大约 90% / 70% / 40%，上下 5 个百分点可以接受）。
- Cybersecurity Analyst 学生的前 10 个常见技能里有安全类技能。
- 用 `student0001@synthetic.example.com` / `Seagas@2026` 能登录，`GET /api/students/profile` 返回 200。

Commit：`feat: regenerate synthetic students against skills library v2`

---

### Phase 4 — JD 职位描述数据集

POC 要求「约 5–10 个 IT 职位的 JD」。这部分**需要人参与采集**，Claude Code 负责工具、格式、清洗、分析和导入。

#### 4.1 来源（按优先级）

1. **公开数据集**（最省时，而且许可条款清楚）：Kaggle 上的公开职位数据集（例如 LinkedIn Job Postings、Data Science Job Postings 这类）。Yong Hin 手动下载后放在 `data/raw/`，Claude Code 负责筛选出 6 个职位的 JD。**使用前检查并记录每个数据集的 license。**
2. **手动收集**：Yong Hin 从 JobStreet Malaysia / LinkedIn / 公司招聘页复制，每条粘贴成 `data/raw/manual/<role_code>/<n>.txt`，第一行写来源 URL 和日期。
3. 不做自动爬虫（规则第 6 条）。

**数量目标：** 6 个职位 × 至少 30 条 = **最少 180 条**，理想是每个职位 50–100 条。（角色说明里写的「每个职位 100–500 条」是上限，不是这个 Sprint 的硬指标。）

#### 4.2 数据格式

`data/jd_dataset/jd_dataset.csv`（清洗后，可以 commit）：

| 列 | 说明 |
|---|---|
| `jd_ref` | `JD-DA-0001` 这种格式 |
| `role_code` | 和 `job_roles.role_code` 一致 |
| `title` | 原始职位名 |
| `company` | ⚠️ 默认填 `"Anonymised"`，不公开公司名 |
| `location`、`seniority`（entry / junior / mid） | |
| `source`（`kaggle:<dataset>` / `manual`）、`source_license`、`collected_date` | |
| `raw_text` | 清洗后的 JD 全文 |

#### 4.3 工具脚本（放 `data/jd_dataset/`）

- `ingest_jds.py`：读 `data/raw/`（Kaggle CSV + manual txt）→ 按职位名关键词归到 6 个 `role_code` → 清洗（去 HTML、去重复的空白、去电话/邮箱、按 `raw_text` 的哈希去重、过滤少于 300 字的）→ 输出 `jd_dataset.csv`。
- `analyse_jd_skills.py`：用技能库的 `skill_name` + `aliases` 做关键词计数（带单词边界，**不用** ambiguous aliases），输出：
  - `jd_skill_frequency.csv`：每个职位每个技能出现在多少比例的 JD 里
  - `unmatched_terms.csv`：用 spaCy noun chunks（如果还没装 spaCy，就用简单的 n-gram）找出高频但技能库里没有的词 → 用来补充 Phase 1.3
  - 建议：出现率 ≥ 50% → required，20–50% → preferred，10–20% → bonus。把建议和 Phase 2 的现有设置对比，输出差异表，**不要自动改 seed**，由 Yong Hin 决定。
- `load_jds.sql` 或 `load_jds.py`：把 `jd_dataset.csv` 导入 `job_descriptions`（`source = 'scraped'`，`profile_id = NULL`，`role_id` 按 `role_code` 查），可以重复执行（用 `jd_ref` 或文本哈希判断是否已导入）。⚠️ `job_descriptions` 没有 `jd_ref` 列，也不能改 schema → 默认把 `jd_ref` 放进 `title` 的前缀，或者用 `raw_text` 的 md5 判断重复。选后者。

#### 4.4 Gold 标注集（给 Sprint 4 的 L1 vs L2 评估用）

- 每个职位随机抽 10 条（seed 固定）= **60 条 JD**，输出 `data/jd_dataset/gold/gold_sample.csv`。
- 建一个空的标注模板 `gold_labels.csv`：`jd_ref, skill_name, importance, evidence_text`。
- Claude Code **可以**先用关键词方法预填一版草稿 `gold_labels_draft.csv`，但**必须由 Yong Hin 人工检查修正后**才能算 gold。在 README 里写清楚：gold 标注不能由要被评估的系统生成，否则评估没有意义。
- 写一份 `ANNOTATION_GUIDE.md`（一页就好）：什么算一个技能、怎么判断 required / preferred（例如 "must have" / "required" vs "nice to have" / "a plus"）、遇到技能库里没有的技能怎么写。

**验收：**
- `jd_dataset.csv` 每个职位 ≥ 30 条，没有重复，没有电话和邮箱。
- `analyse_jd_skills.py` 能跑完，并输出三个文件。
- 导入后：`SELECT jr.role_name, COUNT(*) FROM job_descriptions jd JOIN job_roles jr USING(role_id) WHERE source='scraped' GROUP BY 1;`
- gold 样本 60 条已生成，标注模板和说明都在。

如果 Yong Hin 还没提供原始数据：先把所有脚本和格式做好，用 3–5 条手动示例 JD 测通整个流程，然后在总结里写清楚「等待原始 JD 数据」。

Commit：`feat: JD dataset pipeline, frequency analysis and gold annotation sample`

---

### Phase 5 — 文档、一键加载和收尾

1. **一键加载**：更新 `backend/start_backend.bat`（Yong Hin 写的），在 schema 之后按顺序跑：`seed_skills_library_v2.sql` → `seed_job_role_skills.sql` → 合成学生 → JD 数据。只改加载顺序，其他逻辑不动。
2. **文档**：
   - `data/skills/README.md`：怎么编辑技能库（改 CSV → 跑 build → 跑 test → 跑 seed）
   - 更新 `data/README_synthetic.md`（新的技能数、默认 N、重新生成步骤）
   - `data/jd_dataset/README.md`：来源、license、数量、清洗规则、字段说明
3. **报告草稿**：`docs/report_drafts/dataset_description.md` —— 报告「Dataset description」章节的初稿（英文，IEEE 引用格式）：技能库（来源、分类、数量表）、合成学生数据（生成方法、archetype、分布统计、局限）、JD 数据集（来源、数量、清洗、gold set）、伦理（匿名、合成数据、不用真实学生资料、JD 偏差）。数字全部从生成出来的统计文件读，不要手写。
4. **工作记录**：在总结里附上一段可以直接贴进 Work Log 的中文条目（时间、工作、文件、测试结果），格式跟 `docs/SEAGAS_WorkReport_Part1_By_Yonghin.pdf` 一样。
5. **PR**：push `feature/skills-library-v2`，开 PR 到 `dev`，描述里列出：技能数量变化、alias 修正清单、category 调整（需要 Carl 确认）、合成数据重新生成（组员要重新导入）、JD 数据状态。

**验收：** 在全新的数据库上（`DROP DATABASE seagas_db; CREATE DATABASE seagas_db;`，⚠️ 先确认 Yong Hin 同意，因为会删掉本机数据库）跑完 `start_backend.bat` 全部成功，Swagger 上 `/api/students/skills-library` 返回 120–150 个技能。
Commit：`docs: skills library, synthetic data and JD dataset documentation`

---

## 4. 协作注意（Claude Code 要写进 PR 描述）

| 对象 | 影响 | 要做的事 |
|---|---|---|
| **Aaron**（推荐引擎，技能库共同负责人） | `recommendations_library` 用 `skill_id` 关联；新技能没有推荐资源 | v1 技能名没改，他已有的 seed 不受影响；PR 里附上新增技能清单，请他给重点技能（尤其安全和云）补资源 |
| **Carl**（后端 / schema） | category 调整影响 7 维度分数；以后 NLP 结果写入 `jd_extracted_skills` 时要用 `skills_taxonomy.json` | 请他确认 category → 维度的对应；确认新职位要不要加进 `job_roles` |
| **全组** | 合成数据 UUID 会变 | 合并后每个人都要跑 delete 脚本，然后重新导入 |

---

## 5. 需要 Yong Hin 决定的事（汇总）

| # | 问题 | 默认做法 |
|---|---|---|
| 1 | 安全类技能从 `AI_Digital` 改成 `Technical`？ | 改，并请 Carl 确认 |
| 2 | 要不要加 Business Analyst / DevOps / AI-ML Engineer 职位？ | 这个 Sprint 不加，只提建议 |
| 3 | 合成数据默认数量 500 还是 5000？ | 5000（和已合并的一致），可以用 `--n 500` 生成演示集 |
| 4 | JD 数据来源用哪个 Kaggle 数据集 / 要手动收多少？ | 需要 Yong Hin 提供；脚本先用示例数据测通 |
| 5 | JD 里的公司名要不要保留？ | 匿名化 |
| 6 | Phase 5 的全新数据库测试会删掉本机 `seagas_db` | 执行前先问 |

---

## 6. 完成标准（Definition of Done）

- [ ] 技能库 120–150 个，CSV 单一数据源，`pytest` 全部通过，没有 alias 冲突
- [ ] `seed_skills_library_v2.sql` 和 `seed_job_role_skills.sql` 都可以重复执行
- [ ] 6 个职位都有 required / preferred / bonus，Cybersecurity Analyst 用的是安全技能
- [ ] 合成数据重新生成，三类学生分层依然明显，能登录
- [ ] JD 数据集工具完整；有数据时每个职位 ≥ 30 条；gold 样本 60 条和标注说明都已准备好
- [ ] README、报告 Dataset 章节草稿、Work Log 条目都已写好
- [ ] feature 分支已 push，PR 已开到 `dev`，没有直接 push 到 `dev` / `main`

---

## 附：给 Claude Code 的启动提示（直接复制）

```
读 docs/SPRINT2_SKILLS_DATASET_PLAN.md，按 Phase 0 → 5 执行。
规则：不改 schema.sql；不改名、不删除 v1 的 32 个技能；每个 Phase 验收通过后单独 commit；
只 push feature/skills-library-v2，不要 push dev/main。
遇到「⚠️ 需要确认」先问我；我没回复就用文件里的默认做法，最后汇总告诉我。
先做 Phase 0，把 git status 和数据库连接结果报告给我，再继续。
```
