export function LoadingSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="animate-pulse space-y-4">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="space-y-2">
          <div className="h-4 bg-surface-light rounded w-3/4" />
          <div className="h-4 bg-surface-light rounded w-1/2" />
        </div>
      ))}
    </div>
  );
}
