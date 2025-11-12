'use client';

export default function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-sm">
      <div className="max-w-6xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-white text-xl font-bold">Lagom Training</h1>
          <nav className="hidden md:flex items-center space-x-8">
            <a href="#about" className="text-gray-300 hover:text-white">소개</a>
            <a href="#locations" className="text-gray-300 hover:text-white">지점</a>
            <a href="#membership" className="text-gray-300 hover:text-white">멤버십</a>
            <a href="#contact" className="text-gray-300 hover:text-white">문의</a>
          </nav>
          <div className="flex items-center space-x-4">
            <button className="text-gray-300 hover:text-white">로그인</button>
            <button className="bg-blue-600 text-white px-4 py-2 rounded-full hover:bg-blue-700">
              가입하기
            </button>
          </div>
        </div>
      </div>
    </header>
  );
} 