'use client';

export default function Footer() {
  return (
    <footer className="bg-black text-white py-20 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          <div>
            <h3 className="text-lg font-bold mb-4">About Us</h3>
            <p className="text-gray-400">
              라곰 트레이닝은 건강한 라이프스타일을 추구하는 모든 분들을 위한 프리미엄 피트니스 센터입니다.
            </p>
          </div>

          <div>
            <h3 className="text-lg font-bold mb-4">Contact</h3>
            <div className="space-y-2 text-gray-400">
              <p>Tel: 02-1234-5678</p>
              <p>Email: info@lagom.kr</p>
              <p>강남구 테헤란로 123</p>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-bold mb-4">Follow Us</h3>
            <div className="space-y-2 text-gray-400">
              <p>Instagram</p>
              <p>Facebook</p>
              <p>YouTube</p>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-bold mb-4">Opening Hours</h3>
            <div className="space-y-2 text-gray-400">
              <p>평일: 06:00 - 23:00</p>
              <p>토요일: 09:00 - 18:00</p>
              <p>일요일: 10:00 - 17:00</p>
            </div>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-gray-800">
          <p className="text-center text-gray-400">
            © 2024 Lagom Training. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
} 