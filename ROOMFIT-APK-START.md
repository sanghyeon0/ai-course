# RoomFit 3.1.1 APK 빌드 (별도 브랜치)

이 브랜치는 `main`의 과제 코드를 변경하지 않고 RoomFit APK를 빌드하기 위한 임시 작업 공간입니다.

## 현재 상태
- GitHub Actions 워크플로: `.github/workflows/roomfit-3.1.1-apk.yml` (등록됨)
- 전체 Android 소스 ZIP: **아직 업로드되지 않음**
- APK: **아직 생성되지 않음**

## 소스 업로드
1. ChatGPT 대화에서 `RoomFit-3.1.1-Full-AR-Source.zip`를 휴대폰 또는 PC에 다운로드합니다.
2. GitHub의 이 브랜치로 이동합니다: https://github.com/sanghyeon0/ai-course/tree/roomfit-3.1.1-apk-build
3. `Add file` → `Upload files`를 선택합니다.
4. ZIP을 압축 해제하지 말고 저장소 **최상위 폴더**에 `RoomFit-3.1.1-Full-AR-Source.zip` 이름 그대로 업로드합니다.
5. 변경 사항을 **roomfit-3.1.1-apk-build 브랜치에 직접 커밋**합니다. main 브랜치로 PR을 만들거나 병합하지 않습니다.
6. Actions 탭에서 `RoomFit 3.1.1 Full AR APK` 실행이 성공할 때까지 확인합니다.
7. 성공하면 실행 페이지 → Artifacts → `RoomFit-3.1.1-Full-AR-APK`를 내려받습니다. 압축을 풀면 APK를 얻을 수 있습니다.

빌드 실패 시 실행 화면의 오류 로그를 확인해야 합니다. 이 브랜치에 빌드 워크플로가 설정되어 있는 것과 최종 APK가 정상 빌드되었다는 것은 별개의 상태입니다.

## 보안
이 저장소는 **공개 저장소**입니다. ZIP에 API 키·비밀번호·개인정보가 포함되지 않았는지 확인한 후 업로드해야 합니다. 앱이 개인 용도라면 비공개 저장소에서 빌드하는 편이 낫습니다.
