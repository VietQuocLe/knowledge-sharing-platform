import { Link } from 'react-router-dom'

export interface BreadcrumbItem {
    label: string
    href?: string
}

interface BreadcrumbProps {
    items: BreadcrumbItem[]
    className?: string
}

export function Breadcrumb({ items, className = '' }: BreadcrumbProps) {
    if (!items || items.length === 0) return null

    // Ensure 'Trang chủ' is at the root and not duplicated in the subitems
    const filteredItems = items.filter(
        item => item.href !== '/' && item.label !== 'Trang chủ'
    )

    return (
        <nav aria-label="Breadcrumb" className={`flex text-sm font-medium ${className}`.trim()}>
            <ol className="flex flex-wrap items-center gap-1.5 text-slate-500">
                <li className="flex items-center">
                    <Link
                        to="/"
                        className="flex items-center gap-1 text-slate-400 transition hover:text-slate-900"
                    >
                        <svg
                            className="h-4 w-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                            />
                        </svg>
                        <span>Trang chủ</span>
                    </Link>
                </li>

                {filteredItems.map((item, index) => {
                    const isLast = index === filteredItems.length - 1

                    return (
                        <li key={index} className="flex items-center gap-1.5 min-w-0">
                            <svg
                                className="h-4 w-4 shrink-0 text-slate-300"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    d="M9 5l7 7-7 7"
                                />
                            </svg>

                            {isLast ? (
                                <span
                                    className="truncate text-slate-800 font-semibold max-w-[160px] sm:max-w-[240px] md:max-w-xs"
                                    aria-current="page"
                                >
                                    {item.label}
                                </span>
                            ) : item.href ? (
                                <Link
                                    to={item.href}
                                    className="truncate text-slate-500 transition hover:text-slate-900 max-w-[120px] sm:max-w-[200px]"
                                >
                                    {item.label}
                                </Link>
                            ) : (
                                <span className="truncate text-slate-400 max-w-[120px] sm:max-w-[200px]">
                                    {item.label}
                                </span>
                            )}
                        </li>
                    )
                })}
            </ol>
        </nav>
    )
}
