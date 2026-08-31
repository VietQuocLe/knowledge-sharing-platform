interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

export function Skeleton({ className = '', ...props }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded-xl bg-slate-200/80 ${className}`}
      {...props}
    />
  )
}

export function SubjectCardSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-3xs">
      <div className="flex items-center justify-between">
        <Skeleton className="h-6 w-20 rounded-lg" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-5 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </div>
      <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-16" />
      </div>
    </div>
  )
}

export function DepartmentCardSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 space-y-4 shadow-3xs">
      <Skeleton className="h-28 w-full rounded-xl" />
      <div className="space-y-2">
        <Skeleton className="h-5 w-3/4" />
        <Skeleton className="h-3.5 w-full" />
      </div>
      <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
        <Skeleton className="h-3.5 w-32" />
        <Skeleton className="h-3.5 w-4" />
      </div>
    </div>
  )
}

export function DocumentCardSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-3xs">
      <div className="flex items-center gap-2">
        <Skeleton className="h-5 w-20 rounded-full" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-5 w-full" />
        <Skeleton className="h-4 w-2/3" />
      </div>
      <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
        <Skeleton className="h-6 w-6 rounded-full" />
        <Skeleton className="h-3.5 w-32" />
      </div>
    </div>
  )
}

export function NotebookCardSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-3xs">
      <div className="flex items-center justify-between">
        <Skeleton className="h-9 w-9 rounded-xl" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-5 w-4/5" />
        <Skeleton className="h-3.5 w-1/3" />
      </div>
      <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
        <Skeleton className="h-3.5 w-20" />
        <Skeleton className="h-3.5 w-28" />
      </div>
    </div>
  )
}
