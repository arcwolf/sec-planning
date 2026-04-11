# gh-contribution — GitHub 커밋 히트맵 자동 업데이트

`arcwolf.github.io/project/` 페이지 최상단에 표시되는 커밋 활동 히트맵을 매일 자동 갱신하는 기능.

---

## 📁 파일 구성

| 파일 | 설명 |
|------|------|
| `update-heatmap.py` | 데이터 수집 + 페이지 업데이트 스크립트 |
| `commit-activity.html` | 히트맵 단독 HTML (로컬 확인용) |
| `README.md` | 이 문서 |

**launchd plist (별도 위치):**
```
~/Library/LaunchAgents/com.arcwolf.gh-heatmap-update.plist
```

---

## 🔄 기능 흐름

```
┌──────────────────────────────────────────────────────────┐
│                   launchd (매일 09:00)                    │
│          com.arcwolf.gh-heatmap-update.plist             │
└─────────────────────┬────────────────────────────────────┘
                      │ python3 update-heatmap.py
                      ▼
┌──────────────────────────────────────────────────────────┐
│              1. 활성 리포지토리 목록 조회                  │
│                                                          │
│   gh repo list --json name,pushedAt                      │
│   → 최근 35일 이내 push 있는 repo만 필터링               │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│              2. 커밋 날짜 수집 (최근 31일)                │
│                                                          │
│   for each repo:                                         │
│     gh api repos/arcwolf/{repo}/commits?since=...        │
│     → 날짜(YYYY-MM-DD) 리스트 추출                       │
│   → 커밋 없는 repo 제외                                  │
│   → 커밋 수 내림차순 정렬                                 │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│              3. project.md 현재 내용 취득                 │
│                                                          │
│   gh api repos/arcwolf/arcwolf.github.io                 │
│           /contents/project.md                           │
│   → Base64 디코딩 → 텍스트 추출                          │
│   → 현재 파일 SHA 보존 (PUT 업데이트에 필요)             │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│              4. DATA 블록 치환                            │
│                                                          │
│   정규식: var DATA=\[.*?\];  (DOTALL)                    │
│   → 새로 수집한 JSON 데이터로 교체                        │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│              5. GitHub API PUT — 파일 업데이트            │
│                                                          │
│   gh api repos/arcwolf/arcwolf.github.io                 │
│           /contents/project.md  -X PUT                   │
│   커밋 메시지: "chore: 히트맵 데이터 업데이트 (YYYY-MM-DD)"│
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│              6. GitHub Pages 자동 빌드                    │
│                                                          │
│   arcwolf.github.io → Jekyll 빌드 트리거                 │
│   → https://arcwolf.github.io/project/ 에 반영          │
└──────────────────────────────────────────────────────────┘
```

---

## 🕘 스케줄

| 항목 | 값 |
|------|----|
| 실행 시각 | 매일 **09:00** (로컬 시간) |
| 수집 기간 | 실행 시점 기준 **최근 31일** |
| 대상 | push 기준 최근 35일 이내 활성 repo |

---

## 📋 로그 확인

```bash
# 정상 로그
cat ~/Library/Logs/gh-heatmap-update.log

# 에러 로그
cat ~/Library/Logs/gh-heatmap-update.error.log
```

---

## 🔧 수동 실행

```bash
python3 ~/Desktop/05_Planning/gh-contribution/update-heatmap.py
```

---

## ⚙️ launchd 관리

```bash
# 등록 상태 확인
launchctl list | grep gh-heatmap

# 재등록
launchctl unload ~/Library/LaunchAgents/com.arcwolf.gh-heatmap-update.plist
launchctl load   ~/Library/LaunchAgents/com.arcwolf.gh-heatmap-update.plist
```
