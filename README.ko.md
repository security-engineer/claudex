# claudex

*🌐 [English](README.md) · **한국어***

**Claude Code** 아래에서 **OpenAI Codex (GPT-5.x)** 를 *균형 잡힌 서브 에이전트*로 사용합니다.

Claude가 감독자이자 최종 결정권자이고, Codex는 토큰을 많이 쓰는 작업(코드 탐색, 초안 작성, 제2 의견 리뷰)을 **자신의** 컨텍스트 안에서 처리합니다. 따라서 그 작업은 Anthropic 토큰이 아니라 여러분의 OpenAI/ChatGPT 쿼터로 돌아갑니다. Claude는 무엇이든 적용하기 전에 Codex의 출력을 검토하므로, 품질은 리뷰로 보호되고 — 독립적인 두 프런티어 모델이 교차 검증하면 오히려 *더 좋아지는* 경우가 많습니다.

이 저장소는 플러그인 하나(**`codex-subagent`**)를 담은 **Claude Code 플러그인 마켓플레이스**입니다.

## 플러그인이 설치해 주는 것

- **`codex` MCP 서버** — 번들된 `.mcp.json`으로 자동 등록 (`codex mcp-server` 실행).
- **`codex-subagent` 스킬** — 균형 위임 워크플로우 + 안전 수칙 (필요할 때만 로드되어, 쓰기 전엔 컨텍스트 비용 0).
- **`/codex <작업>`** — 집중된 작업 하나를 Codex에 위임한 뒤 검토.
- **`/cross-review <대상>`** — 사용자가 라운드 수를 정하는, 경계가 있는 Claude↔Codex 피드백 루프.
- **SessionStart 훅** — 매 세션마다 짧은 상시 정책을 주입해 Claude가 기본적으로 균형 자세로 동작 (always-on).

## 사전 요건

1. **Claude Code** 설치.
2. **Codex CLI**를 Claude Code와 **같은 환경**에 설치하고 로그인 (Claude를 컨테이너에서 실행한다면 Codex도 그 컨테이너 안에 설치·로그인되어 있어야 함):
   ```bash
   curl -fsSL https://chatgpt.com/codex/install.sh | sh   # 설치
   codex login                                            # 또는: codex login --device-auth
   codex login status                                     # 확인
   ```
3. `~/.codex/config.toml`에서 Codex 모델/추론 강도 선택 (MCP 서버가 이를 상속):
   ```toml
   model = "gpt-5.5"
   model_reasoning_effort = "xhigh"
   ```

## 설치

```bash
# 1) 이 저장소를 마켓플레이스로 추가 (GitHub repo · URL · 로컬 경로 모두 가능)
claude plugin marketplace add security-engineer/claudex

# 2) 플러그인 설치
claude plugin install codex-subagent@claudex

# 3) Claude Code 재시작 → MCP 서버·훅·스킬·명령 로드
```

로컬 개발 설치 (GitHub 불필요):

```bash
claude plugin marketplace add /absolute/path/to/claudex
claude plugin install codex-subagent@claudex
```

확인:

```bash
claude plugin list
claude mcp list          # codex 가 ✔ Connected 여야 함
# 세션 안에서:  /mcp   →   /codex hello   →   /cross-review <대상>
```

---

## 사용법

**역할 분담**

- **Claude (Opus 4.8)** = 감독자 — 최종 판단, 편집 적용, 테스트 실행, 의견 조율.
- **Codex (GPT-5.x, xhigh)** = 서브 에이전트 — 토큰을 많이 쓰는 탐색, 초안, 독립 리뷰, 엣지케이스 헌팅. Anthropic 토큰이 **아니라** 여러분의 OpenAI/ChatGPT 쿼터로 동작.

평소처럼 작업하면 됩니다 — SessionStart 정책이 Claude가 적절히 위임하도록 유도합니다. 아래 명령으로 직접 구동할 수도 있습니다.

### `/codex <작업>`

집중된 작업 하나를 Codex에 위임한 뒤, 적용 전에 결과를 검토합니다.

**흐름:** 파일 범위 지정 → 위임(MCP 또는 `codex exec`) → 비판적으로 검토 → Claude가 적용 + 테스트.

**예시**
- `/codex src/auth/ 의 diff를 리뷰하고 엣지케이스를 나열해줘`
- `/codex utils/date.py 의 중복 제거 리팩터 초안을 작성해줘`
- `/codex tests/test_api.py 의 실패 테스트 근본 원인을 찾아줘`

Codex는 기본적으로 **읽기 전용(read-only)** 으로 동작하며, 패치가 명시적으로 필요할 때만 씁니다. 비밀값이나 거대한 데이터셋 폴더는 범위에 넣지 마세요.

### `/cross-review <대상> [rounds=N] [style=ab|independent|debate]`

경계가 있는 Claude↔Codex 피드백 루프를 돌린 뒤, Claude가 판정을 내립니다.

**인자**
- `대상` — 파일, diff(예: "the staged diff"), 또는 질문/주제. `key=value` 플래그가 아닌 나머지 전부.
- `rounds=N` — 비판↔반론 라운드를 **몇 번** 돌릴지 직접 선택. 기본 **2**. 절대 상한 **5**(그 이상을 줘도 5로 클램프되어, 5회를 절대 넘기지 않음).
- `style` — `ab`(기본: 한쪽이 작성, 다른 쪽이 비판), `independent`(둘이 따로 풀고 Claude가 비교), `debate`(적대적 핑퐁).

**루프 (style `ab`)**
1. Claude가 입장/초안을 제시.
2. Codex가 비판 — 버그, 엣지케이스, 불일치 지점, 각각 `file:line` 포함.
3. Claude가 각 지점을 수용(수정)하거나 반론.
4. 수렴 체크 — 해결되거나 사소하면 조기 종료.
5. `rounds`까지 반복한 뒤 **결정적으로** 종료.
6. 상한에서도 수렴하지 않으면 → Claude(감독자)가 최종 결정을 내리고 **미해결 불일치를 사용자에게 보고**하여 사람이 타이브레이크. **무한 루프 없음.**

**예시**
- `/cross-review src/auth.py` — 2라운드, A→B.
- `/cross-review the staged diff rounds=4` — 최대 4라운드.
- `/cross-review "이 작업에 큐 vs 크론?" style=independent` — 독립 후 비교.
- `/cross-review payments/refund.py rounds=3 style=debate` — 3라운드 적대적 토론.

**비용 메모:** 교차 리뷰는 토큰·지연을 더 써서 품질을 얻는 방식입니다 — 전부가 아니라 중요하거나 논쟁적인 코드에 쓰세요. Codex 쪽 = OpenAI 토큰, Claude의 조율/판정 = Anthropic 토큰.

### `codex-subagent` 스킬

**필요할 때만** 로드됩니다(쓰기 전엔 컨텍스트 비용 0). 작업이 탐색·초안·엣지케이스 헌팅에 무겁거나 독립적인 제2 의견이 필요할 때 — 또는 Codex/토큰 절약 위임을 언급할 때 — Claude가 자동으로 호출합니다. 균형 자세, 위임 프롬프트 템플릿, 안전 수칙이 담겨 있습니다. 명시적으로 부르려면: "codex-subagent 워크플로우를 써줘."

### MCP 도구 (고급 / 직접 제어)

플러그인이 **`codex`** MCP 서버를 자동 등록합니다. 설치 후 도구가 세션에 로드되도록 **Claude Code를 재시작**하세요.

- **`codex`** — Codex 세션 시작. 주요 파라미터: `prompt`(필수), `cwd`(코드 폴더로 범위 지정), `sandbox`(`read-only` 기본 · 패치용 `workspace-write` · `danger-full-access`), `model`(기본값은 `~/.codex/config.toml`), `approval-policy`(비대화형은 `never`). `threadId` 반환.
- **`codex-reply`** — 스레드 이어가기: `threadId` + `prompt`. 다회차 `/cross-review`의 동력.

**CLI 폴백 (결정적, 재시작 전에도 동작):**
```bash
codex exec -C <code-dir> -s read-only --skip-git-repo-check "<focused task>"
```

---

## 설정

- **Codex 모델 / 추론 강도** — `~/.codex/config.toml` (`model`, `model_reasoning_effort`). MCP 서버와 `codex exec`가 이를 상속합니다. 비용을 아끼려고 모델을 낮추지 마세요 — 그게 실제로 품질을 떨어뜨리는 유일한 변경입니다.
- **교차 리뷰 라운드** — 호출 시 `rounds=N` (기본 2, 상한 5).
- **샌드박스** — 기본 읽기 전용. Codex가 패치를 만들어야 할 때만 `workspace-write`.

## 안전 수칙

- 비밀값, `.env`, 개인 키, 자격증명, 토큰, SSH/클라우드 인증을 Codex에 절대 보내지 마세요.
- Codex에 거대한 데이터셋 폴더를 스캔시키지 마세요 — `-C <code-dir>` / `cwd`로 범위를 좁히세요.
- 패치가 필요하지 않으면 Codex는 읽기 전용으로 유지하세요.
- Claude는 적용 전에 항상 Codex 출력을 검토합니다.

## 문제 해결

| 증상 | 해결 |
|---|---|
| `/codex`, `/cross-review`, codex MCP 도구가 안 보임 | Claude Code 재시작 — MCP·명령은 세션 시작 시 로드됨 |
| codex MCP 미연결 | `codex login status`; Claude Code와 **같은** 환경에 codex 설치·로그인 |
| Codex 인증 오류 | `codex login` (또는 `codex login --device-auth`) |
| `codex exec`가 "Not inside a trusted directory" 오류 | `--skip-git-repo-check` 와 `-C <code-dir>` 추가 |
| Codex가 느림 / 너무 많이 스캔 | 항상 `-C <code-dir>` / `cwd` 전달; 거대한 repo 루트를 가리키지 말 것 |

## 업데이트 배포

이 플러그인은 **github.com/security-engineer/claudex**에 있습니다. 변경을 배포하려면:

```bash
# plugins/codex-subagent/.claude-plugin/plugin.json 의 "version" 을 올린 뒤:
git add -A && git commit -m "describe the change" && git push
```

사용자는 `claude plugin update codex-subagent@claudex`로 받아갑니다(적용하려면 재시작).

## 라이선스

MIT — [LICENSE](LICENSE) 참고.
