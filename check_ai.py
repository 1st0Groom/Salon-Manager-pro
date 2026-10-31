import os
import google.generativeai as genai

# ==========================================
# Set GOOGLE_API_KEY in the environment; never paste it into source.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise SystemExit("Set the GOOGLE_API_KEY environment variable before running this script.")
# ==========================================

genai.configure(api_key=GOOGLE_API_KEY)

print("--------------------------------------------------")
print("🤖 구글 AI 서버에 접속 중...")
print("--------------------------------------------------")

try:
    # 사용 가능한 모든 모델 목록을 가져옵니다.
    models = genai.list_models()
    
    found_any = False
    print("\n✅ 사용 가능한 모델 목록:")
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            print(f" - {m.name}")
            found_any = True
            
    if not found_any:
        print("❌ 사용 가능한 모델이 없습니다. API 키 권한을 확인하세요.")
    else:
        print("\n🎉 성공! 위 목록에 있는 이름 중 하나를 main.py에 적으면 됩니다.")
        print("추천: 'models/gemini-1.5-flash' 또는 'models/gemini-pro'")

except Exception as e:
    print(f"\n❌ 에러 발생: {e}")
    print("팁: API 키가 정확한지, 'Google AI Studio'에서 만든 키가 맞는지 확인하세요.")