# SRTgo: K-Train (KTX, SRT) Reservation Assistant
[![Upload Python Package](https://github.com/lapis42/srtgo/actions/workflows/python-publish.yml/badge.svg)](https://github.com/lapis42/srtgo/actions/workflows/python-publish.yml)
[![Downloads](https://static.pepy.tech/badge/srtgo)](https://pepy.tech/project/srtgo)
[![Downloads](https://static.pepy.tech/badge/srtgo/month)](https://pepy.tech/project/srtgo)
[![Python version](https://img.shields.io/pypi/pyversions/srtgo)](https://pypistats.org/packages/srtgo)

> [!NOTE]
> 공정한 예매 문화 조성을 위해 본 프로젝트의 개발 및 지원을 중단하기로 결정했습니다. 양해 부탁드립니다.

> [!WARNING]
> 본 프로그램의 모든 상업적, 영리적 이용을 엄격히 금지합니다. 본 프로그램 사용에 따른 민형사상 책임을 포함한 모든 책임은 사용자에게 있으며, 본 프로그램의 개발자는 민형사상 책임을 포함한 어떠한 책임도 부담하지 않습니다. 본 프로그램을 내려받음으로써 모든 사용자는 위 사항에 이의 없이 동의하는 것으로 간주됩니다.

---
> [!NOTE]
> I have decided to discontinue the development and support for this project. Thank you for your understanding.

> [!WARNING]
> All commercial and profit-making use of this program is strictly prohibited. Use of this program is at your own risk, and the developers of this program shall not be liable for any liability, including civil or criminal liability. By downloading this program, all users are deemed to agree to the above terms without any objection.

## 코레일+ 통합 전환 대응

기본 메뉴는 코레일 통합 계정으로 KTX·SRT를 함께 조회하고 예매하도록 변경했습니다.
기존 `KTX` 키체인 계정을 사용하며, SRT 계정 정보를 자동으로 복사하지 않습니다.
서울역·수서역을 같은 역 목록에서 선택할 수 있습니다. 통합회원 전환이 필요한 계정은
[공식 안내](https://info.korail.com/info/selectBbsNttView.do?bbsNo=199&key=911&nttNo=27109&pageIndex=1&searchCnd=all)를 확인하세요.

### 실행

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/srtgo
```

`로그인 설정`에서 코레일+ 통합 계정을 등록하고 `예매 시작`에서 구간·날짜·인원을 선택합니다.
카드 결제는 기본적으로 꺼져 있습니다. 기존 SRT 전용 모듈은 호환성을 위해 남겨두지만
기본 메뉴에서는 사용하지 않습니다.

### 검증 범위와 현재 제한

2026-11-17 KST 점검에서 기존 코레일 모바일 API를 통한 부산→서울 조회는 서버의
`MACRO ERROR` / 앱 업데이트 안내로 거부됐습니다. **현재 실서버 조회·로그인·예매 성공은
검증되지 않았습니다.** 이 변경은 기존 코레일 API 호환 경로의 통합 전환 준비이며,
공식 코레일+ 신규 API 구현이나 서비스 거부 문제 해결을 보장하지 않습니다.
서버가 거부하면 반복 요청을 중단하며, 예매는 공식 코레일+ 앱/웹에서 진행해야 합니다.

예약 요청 이후 통신·응답 처리 오류가 발생하면 중복 예약을 막기 위해 자동 재시도를 중단합니다.
이때 코레일+ 예약 내역을 먼저 확인하세요. 조회 결과의 순서가 바뀌어도 선택한 열차의
번호·날짜·시간·구간으로 대상을 다시 찾습니다.

네트워크와 실제 계정을 사용하지 않는 회귀 테스트:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

## Acknowledgments
- This project includes code from [SRT](https://github.com/ryanking13/SRT) by ryanking13, licensed under the MIT License, and [korail2](https://github.com/carpedm20/korail2) by carpedm20, licensed under the BSD License.
