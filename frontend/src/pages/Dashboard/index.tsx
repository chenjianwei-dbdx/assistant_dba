export default function Dashboard() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-sm text-gray-500">Total Queries</div>
          <div className="text-3xl font-bold text-blue-600">1,234</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-sm text-gray-500">Active Connections</div>
          <div className="text-3xl font-bold text-green-600">56</div>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg">
          <div className="text-sm text-gray-500">Slow Queries</div>
          <div className="text-3xl font-bold text-yellow-600">12</div>
        </div>
        <div className="bg-red-50 p-4 rounded-lg">
          <div className="text-sm text-gray-500">Failed Jobs</div>
          <div className="text-3xl font-bold text-red-600">3</div>
        </div>
      </div>
    </div>
  )
}
