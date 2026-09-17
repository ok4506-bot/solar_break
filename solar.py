"""
    [함수]   ask_number, ask_yes_no, choose_zone, decide_limits, input_floors,
             sum_floor_area, largest_floor_area, count_extra_floors,
             judge, required_setback, check_solar,
             print_ratio, print_solar_table, draw_section, main
    [조건문] if / elif / else  → judge, required_setback, decide_limits, 입력 검증 등
    [반복문] for   → 연면적 합산, 가장 넓은 층 찾기, 층별 높이 누적, 표·단면도 출력
             while → 올바른 값이 들어올 때까지 다시 묻기, 더 올릴 수 있는 층수 세기


기준: 서울특별시 도시계획 조례(조례 제10139호, 2026. 7. 13. 시행) 제44조·제48조·제51조제2항제9호
      건축법 시행령 제86조제1항, 서울특별시 건축 조례 제35조제1항
"""

# ─────────────────────────────────────────────────────────────
# 0. 자료: dictionary와 list
# ─────────────────────────────────────────────────────────────
# bcr 건폐율 한도(%), far 용적률 한도(%),
# far_relaxed 소규모 건축물 완화 시 한도, far_downtown 서울도심 안일 때 한도,
# solar 정북일조 적용 여부(전용주거·일반주거지역만 True)
ZONES = [
    {"name": "제1종전용주거지역", "bcr": 50, "far": 100, "solar": True},
    {"name": "제2종전용주거지역", "bcr": 40, "far": 120, "solar": True},
    {"name": "제1종일반주거지역", "bcr": 60, "far": 150, "solar": True},
    {"name": "제2종일반주거지역", "bcr": 60, "far": 200, "far_relaxed": 250, "solar": True},
    {"name": "제3종일반주거지역", "bcr": 50, "far": 250, "far_relaxed": 300, "solar": True},
    {"name": "준주거지역",       "bcr": 60, "far": 400, "solar": False},
    {"name": "중심상업지역",     "bcr": 60, "far": 1000, "far_downtown": 800, "solar": False},
    {"name": "일반상업지역",     "bcr": 60, "far": 800,  "far_downtown": 600, "solar": False},
    {"name": "근린상업지역",     "bcr": 60, "far": 600,  "far_downtown": 500, "solar": False},
    {"name": "유통상업지역",     "bcr": 60, "far": 600,  "far_downtown": 500, "solar": False},
    {"name": "전용공업지역",     "bcr": 60, "far": 200, "solar": False},
    {"name": "일반공업지역",     "bcr": 60, "far": 200, "solar": False},
    {"name": "준공업지역",       "bcr": 60, "far": 400, "solar": False},
    {"name": "보전녹지지역",     "bcr": 20, "far": 50, "solar": False},
    {"name": "생산녹지지역",     "bcr": 20, "far": 50, "solar": False},
    {"name": "자연녹지지역",     "bcr": 20, "far": 50, "solar": False},
    {"name": "한도 직접 입력 (주거지역, 지구단위계획 등)", "bcr": None, "far": None, "solar": True},
]

SOLAR_BREAK_HEIGHT = 10    # 이 높이(m)까지는
SOLAR_MIN_SETBACK = 1.5    # 1.5m 이상 띄우고, 넘으면 높이의 1/2


# ─────────────────────────────────────────────────────────────
# 1. 입력 받기  (소수 판별기의 user_input에 해당)
# ─────────────────────────────────────────────────────────────

# [함수] 숫자 하나를 입력받는다. 잘못 넣으면 안내하고 다시 묻는다.
def ask_number(question, default, minimum=0, allow_minimum=False, integer=False):
    # [반복문] while: 올바른 값이 들어올 때까지 계속 묻는다
    while True:
        text = input(f"{question} [{default}]: ").strip().replace(",", "")

        # [조건문] 그냥 Enter면 예시 값을 쓴다
        if text == "":
            return default

        try:
            if integer:
                value = int(text)
            else:
                value = float(text)
        except ValueError:
            if integer:
                print("  → 정수가 아닙니다. 정수로 다시 입력하세요.")
            else:
                print("  → 숫자가 아닙니다. 숫자로 다시 입력하세요.")
            continue

        # [조건문] 범위 검사
        if allow_minimum and value < minimum:
            print(f"  → {minimum} 이상의 값으로 다시 입력하세요.")
        elif not allow_minimum and value <= minimum:
            print(f"  → {minimum}보다 큰 값으로 다시 입력하세요.")
        else:
            return value


# [함수] 예/아니오를 입력받는다.
def ask_yes_no(question):
    # [반복문] while
    while True:
        text = input(f"{question} (y/n) [n]: ").strip().lower()
        # [조건문]
        if text in ["", "n", "no", "아니오"]:
            return False
        elif text in ["y", "yes", "예", "네"]:
            return True
        else:
            print("  → y 또는 n으로 다시 입력하세요.")


# [함수] 용도지역 목록을 보여주고 하나를 고르게 한다.
def choose_zone():
    print("\n용도지역")
    # [반복문] for: 목록을 번호와 함께 출력
    for i, zone in enumerate(ZONES):
        print(f"  {i + 1:>2}. {zone['name']}")

    number = ask_number("번호를 고르세요", 4, minimum=1, allow_minimum=True, integer=True)
    # [반복문] while + [조건문]: 목록에 없는 번호면 다시
    while number > len(ZONES):
        print(f"  → 1부터 {len(ZONES)} 사이의 번호로 다시 입력하세요.")
        number = ask_number("번호를 고르세요", 4, minimum=1, allow_minimum=True, integer=True)
    return ZONES[number - 1]


# [함수] 고른 용도지역에 따라 실제로 적용할 건폐율·용적률 한도를 정한다.
def decide_limits(zone):
    bcr_limit = zone["bcr"]
    far_limit = zone["far"]
    basis = "서울시 조례"

    # [조건문] if / elif / elif: 용도지역의 종류에 따라 갈라진다
    if zone["bcr"] is None:
        bcr_limit = ask_number("건폐율 한도(%)", 60)
        far_limit = ask_number("용적률 한도(%)", 200)
        basis = "직접 입력"
    elif "far_relaxed" in zone:
        # 조례 제51조제2항제9호. 대상 여부는 서울시장이 따로 정한 운영기준으로 판단한다.
        if ask_yes_no("소규모 건축물 용적률 완화를 적용할까요?"):
            far_limit = zone["far_relaxed"]
            basis = "완화 적용"
    elif "far_downtown" in zone:
        if ask_yes_no("서울도심 안의 대지인가요?"):
            far_limit = zone["far_downtown"]
            basis = "서울도심"

    return bcr_limit, far_limit, basis


# [함수] 층수와 층별 바닥면적·층고를 입력받아 list 두 개로 돌려준다.
def input_floors():
    default_areas = [160, 160, 160, 120]
    default_heights = [3.3, 3.0, 3.0, 3.0]

    print("\n지상층")
    count = ask_number("지상 층수(정수)", 4, minimum=1, allow_minimum=True, integer=True)

    areas = []
    heights = []
    # [반복문] for: 아래층부터 한 층씩 입력받아 list에 쌓는다
    for i in range(count):
        # [조건문] 예시 값은 4개뿐이라, 그 위층은 바로 아래층 값을 예시로 쓴다
        if i < len(default_areas):
            d_area, d_height = default_areas[i], default_heights[i]
        else:
            d_area, d_height = areas[-1], heights[-1]
        areas.append(ask_number(f"  {i + 1}층 바닥면적(㎡)", d_area))
        heights.append(ask_number(f"  {i + 1}층 층고(m)", d_height))
    return areas, heights


# ─────────────────────────────────────────────────────────────
# 2. 반복문으로 계산
# ─────────────────────────────────────────────────────────────

# [함수] 연면적 = 층별 바닥면적의 합
def sum_floor_area(areas):
    total = 0
    # [반복문] for
    for a in areas:
        total = total + a
    return total


# [함수] 건축면적 어림 = 가장 넓은 층의 바닥면적
def largest_floor_area(areas):
    biggest = 0
    # [반복문] for + [조건문] if
    for a in areas:
        if a > biggest:
            biggest = a
    return biggest


# [함수] 남은 연면적으로 같은 크기의 층을 몇 개 더 올릴 수 있는지 센다.
def count_extra_floors(remaining_area, floor_area):
    count = 0
    # [반복문] while: 한 층 넣을 면적이 남아 있는 동안 반복
    while remaining_area >= floor_area:
        remaining_area = remaining_area - floor_area
        count = count + 1
    return count


# ─────────────────────────────────────────────────────────────
# 3. 조건문으로 판정  (소수 판별기의 prime에 해당)
# ─────────────────────────────────────────────────────────────

# [함수] 한도 이하면 '적합', 넘으면 '초과'
def judge(value, limit):
    # [조건문] if / else
    if value <= limit:
        return "적합"
    else:
        return "초과"


# [함수] 어떤 높이에서 정북 경계선으로부터 띄워야 하는 거리(m)
def required_setback(height):
    # [조건문] if / else
    if height <= SOLAR_BREAK_HEIGHT:
        return SOLAR_MIN_SETBACK
    else:
        return height / 2


# [함수] 층마다 돌면서 상단 높이를 누적하고, 필요한 이격거리와 비교한다.
def check_solar(heights, setback):
    rows = []
    top = 0
    # [반복문] for
    for i, h in enumerate(heights):
        bottom = top
        top = top + h
        need = required_setback(top)          # 함수 안에서 다른 함수를 부른다
        rows.append({
            "floor": i + 1,
            "bottom": bottom,
            "top": top,
            "need": need,
            "ok": setback >= need,
        })
    return rows


# ─────────────────────────────────────────────────────────────
# 4. 결과 출력
# ─────────────────────────────────────────────────────────────

# [함수] 건폐율·용적률 한 줄과 막대 그래프
def print_ratio(name, value, limit, verdict, note):
    bar_length = 40                       # 막대 전체 = 한도의 125%
    limit_pos = int(bar_length * 0.8)     # 한도선은 80% 지점
    filled = min(bar_length, int(value / (limit * 1.25) * bar_length))

    bar = ""
    # [반복문] for + [조건문] if / elif / else: 막대를 한 칸씩 만든다
    for i in range(bar_length):
        if i == limit_pos:
            bar = bar + "|"
        elif i < filled:
            bar = bar + "#"
        else:
            bar = bar + "."

    print(f"\n{name}  {value:6.1f}%  / 한도 {limit:g}%   → {verdict}")
    print(f"  [{bar}]   (| = 한도)")
    print(f"  {note}")


# [함수] 층별 정북일조 표
def print_solar_table(rows, setback):
    print("\n   층   상단높이   필요이격   현재이격   판정")
    print("  ─────────────────────────────────────────────")
    # [반복문] for: 단면도처럼 꼭대기 층부터 출력
    for r in reversed(rows):
        # [조건문]
        if r["ok"]:
            result = "적합"
        else:
            result = f"{r['need'] - setback:.2f}m 부족"
        print(f"  {r['floor']:>2}층  {r['top']:7.1f}m  {r['need']:7.2f}m  {setback:7.2f}m   {result}")


# [함수] 글자로 그리는 정북 방향 단면도 (가로 한 칸 = 0.5m)
def draw_section(rows, setback, depth):
    step = 0.5
    total_height = rows[-1]["top"]
    width_m = max(setback + depth, total_height / 2) + 1
    columns = int(width_m / step)

    print("\n정북 방향 단면   ← 북          남 →")
    print("  ¦ 인접 대지경계선   / 지을 수 없는 범위   X 제한을 넘은 부분   = 계획 건물\n")

    # [반복문] for: 꼭대기 층부터 한 줄씩
    for r in reversed(rows):
        line = "  ¦"
        # [반복문] 안쪽 for: 왼쪽(북)에서 오른쪽(남)으로 한 칸씩
        for c in range(columns):
            x = c * step                          # 경계선에서 이 칸까지의 거리(m)
            inside_building = setback <= x < setback + depth
            beyond_line = x < r["need"]           # 사선제한선보다 북쪽인가

            # [조건문] if / elif / elif / else
            if inside_building and beyond_line:
                line = line + "X"
            elif inside_building:
                line = line + "="
            elif beyond_line:
                line = line + "/"
            else:
                line = line + " "
        print(f"{line}  {r['floor']}층 {r['top']:.1f}m")

    print("  ¦" + "‾" * columns)


# ─────────────────────────────────────────────────────────────
# 5. main(): 위 함수들을 순서대로 부른다
# ─────────────────────────────────────────────────────────────
def main():
    print("=" * 56)
    print(" 서울의 이 대지에 이 건물, 지을 수 있을까")
    print(" (Enter만 누르면 [ ] 안의 예시 값이 들어갑니다)")
    print("=" * 56)

    # (1) 입력 받기
    print("\n대지")
    site_area = ask_number("대지면적(㎡)", 330)
    zone = choose_zone()
    bcr_limit, far_limit, basis = decide_limits(zone)
    areas, heights = input_floors()

    print("\n정북 방향 배치")
    setback = ask_number("정북 경계선에서 외벽까지(m)", 2, minimum=0, allow_minimum=True)
    depth = ask_number("건물 남북 깊이(m)", 11)

    # (2) 반복문으로 계산
    total_area = sum_floor_area(areas)
    building_area = largest_floor_area(areas)
    bcr = building_area / site_area * 100
    far = total_area / site_area * 100

    # (3) 조건문으로 판정
    bcr_verdict = judge(bcr, bcr_limit)
    far_verdict = judge(far, far_limit)
    solar_rows = check_solar(heights, setback)

    solar_over_count = 0
    # [반복문] for + [조건문] if: 사선제한에 걸린 층수 세기
    for r in solar_rows:
        if zone["solar"] and not r["ok"]:
            solar_over_count = solar_over_count + 1

    # (4) 결과 출력
    print("\n" + "=" * 56)
    print(f" 검토 결과: {zone['name']}")
    print(f" 적용 한도({basis}): 건폐율 {bcr_limit:g}%, 용적률 {far_limit:g}%")
    print("=" * 56)

    max_building_area = site_area * bcr_limit / 100
    max_total_area = site_area * far_limit / 100
    print_ratio("건폐율", bcr, bcr_limit, bcr_verdict,
                f"건축면적 {building_area:.1f}㎡ / 허용 {max_building_area:.1f}㎡")
    print_ratio("용적률", far, far_limit, far_verdict,
                f"연면적 {total_area:.1f}㎡ / 허용 {max_total_area:.1f}㎡")

    remaining = max_total_area - total_area
    top_floor_area = areas[-1]
    print()
    # [조건문] if / elif / else
    if far_verdict == "초과":
        print(f"연면적을 {-remaining:.1f}㎡ 줄여야 용적률 한도에 맞습니다.")
    else:
        extra = count_extra_floors(remaining, top_floor_area)
        if extra == 0:
            print(f"남은 연면적은 {remaining:.1f}㎡로, 꼭대기 층({top_floor_area:.1f}㎡)과 같은 층을 더 올리기에는 모자랍니다.")
        else:
            print(f"남은 연면적은 {remaining:.1f}㎡입니다. 꼭대기 층({top_floor_area:.1f}㎡)과 같은 크기로 {extra}개 층을 더 올릴 수 있습니다.")

    # [조건문] 정북일조는 전용주거·일반주거지역에만 적용
    if zone["solar"]:
        draw_section(solar_rows, setback, depth)
        print_solar_table(solar_rows, setback)
    else:
        print(f"\n{zone['name']}은 정북일조 사선제한 대상이 아닙니다.")

    # 종합 판정
    problems = []
    if bcr_verdict == "초과":
        problems.append(f"건폐율이 한도를 {bcr - bcr_limit:.1f}%p 넘습니다")
    if far_verdict == "초과":
        problems.append(f"용적률이 한도를 {far - far_limit:.1f}%p 넘습니다")
    if solar_over_count > 0:
        problems.append(f"{solar_over_count}개 층이 정북일조 사선제한에 걸립니다")

    print("\n" + "=" * 56)
    if len(problems) == 0:
        print(" 종합: 검토한 항목 모두 적합합니다.")
    else:
        # [반복문] for
        for p in problems:
            print(f" 종합: {p}.")
    print("=" * 56)


if __name__ == "__main__":
    main()
