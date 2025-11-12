'use client';

export default function CollaborationSection() {
  return (
    <section className="bg-black text-white py-20 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
          <h2 className="text-2xl font-bold">Collaboration</h2>
        </div>

        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <p className="text-lg">Support</p>
            <p className="text-gray-400">지지</p>
          </div>
          <div className="flex items-center gap-4">
            <p className="text-lg">Teamwork</p>
            <p className="text-gray-400">팀워크</p>
          </div>
          <div className="flex items-center gap-4">
            <p className="text-lg">Sustainability</p>
            <p className="text-gray-400">지속 가능성</p>
          </div>
          <div className="flex items-center gap-4">
            <p className="text-lg">Community</p>
            <p className="text-gray-400">공동체</p>
          </div>
        </div>

        <div className="mt-20">
          <p className="text-gray-400 mb-4">라곰은 특별하지 않습니다.</p>
          <div className="flex items-center gap-2">
            <p className="text-lg">라곰은</p>
            <p className="text-gray-400">하나의 거대한</p>
          </div>
          <div className="flex items-center gap-2">
            <p className="text-gray-400">피트니스</p>
            <p className="text-lg">커뮤니티</p>
            <p className="text-gray-400">입니다.</p>
          </div>
        </div>

        <div className="mt-20 grid grid-cols-3 gap-4">
          <div className="aspect-square relative">
            <img src="/images/training-1.jpg" alt="Training 1" className="w-full h-full object-cover" />
          </div>
          <div className="aspect-square relative">
            <img src="/images/training-2.jpg" alt="Training 2" className="w-full h-full object-cover" />
          </div>
          <div className="aspect-square relative">
            <img src="/images/training-3.jpg" alt="Training 3" className="w-full h-full object-cover" />
          </div>
        </div>
      </div>
    </section>
  );
} 