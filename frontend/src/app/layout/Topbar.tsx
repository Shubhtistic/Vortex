function Topbar() {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-800">Vortex</h1>
        <div className="flex items-center gap-4">
          <button className="text-gray-500 hover:text-gray-700">
            Notifications
          </button>
          <div className="w-8 h-8 rounded-full bg-blue-500" />
        </div>
      </div>
    </header>
  )
}

export default Topbar
