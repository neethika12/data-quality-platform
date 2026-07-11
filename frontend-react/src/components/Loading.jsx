export default function Loading() {
  return (
    <div className="flex flex-col items-center justify-center p-12">
      <div className="w-12 h-12 rounded-full border-4 border-gray-200 dark:border-gray-700 border-t-primary animate-spin"></div>
      <p className="mt-4 text-gray-600 dark:text-gray-400 font-medium">Loading...</p>
    </div>
  )
}
