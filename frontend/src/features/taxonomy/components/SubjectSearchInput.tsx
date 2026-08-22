import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { BookOpen, Search, X } from 'lucide-react'
import { useSearchSubjects } from '../hooks/useSearchSubjects'

interface SubjectSearchInputProps {
    onSelect?: (subject: { id: number; name: string; code: string }) => void
    placeholder?: string
}

export function SubjectSearchInput({ onSelect, placeholder = "Tìm kiếm môn học..." }: SubjectSearchInputProps) {
    const [query, setQuery] = useState('')
    const [debouncedQuery, setDebouncedQuery] = useState('')
    const [isOpen, setIsOpen] = useState(false)
    const [activeIndex, setActiveIndex] = useState(-1)
    const containerRef = useRef<HTMLDivElement>(null)
    const navigate = useNavigate()

    // Debounce query
    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedQuery(query)
        }, 300)
        return () => clearTimeout(handler)
    }, [query])

    const showDropdown = isOpen && debouncedQuery.trim().length >= 2
    const { data: subjects = [], isLoading } = useSearchSubjects(debouncedQuery)

    // Handle click outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    // Reset active index when results change
    useEffect(() => {
        setActiveIndex(-1)
    }, [subjects])

    const handleSelect = (subject: { id: number; name: string; code: string }) => {
        if (onSelect) {
            onSelect(subject)
            setQuery(subject.name)
        } else {
            setQuery('')
            navigate(`/subjects/${subject.id}`)
        }
        setIsOpen(false)
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (!showDropdown) return

        if (e.key === 'ArrowDown') {
            e.preventDefault()
            setActiveIndex((prev) => (subjects.length > 0 ? (prev + 1) % subjects.length : -1))
        } else if (e.key === 'ArrowUp') {
            e.preventDefault()
            setActiveIndex((prev) => (subjects.length > 0 ? (prev - 1 + subjects.length) % subjects.length : -1))
        } else if (e.key === 'Enter') {
            e.preventDefault()
            if (activeIndex >= 0 && activeIndex < subjects.length) {
                handleSelect(subjects[activeIndex])
            }
        } else if (e.key === 'Escape') {
            e.preventDefault()
            setIsOpen(false)
        }
    }

    const highlightMatch = (text: string, highlight: string) => {
        if (!highlight.trim()) return <span>{text}</span>
        const regex = new RegExp(`(${highlight.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')})`, 'gi')
        const parts = text.split(regex)
        return (
            <span>
                {parts.map((part, i) =>
                    regex.test(part) ? (
                        <strong key={i} className="font-bold text-indigo-700 bg-indigo-50/80">
                            {part}
                        </strong>
                    ) : (
                        <span key={i}>{part}</span>
                    )
                )}
            </span>
        )
    }

    return (
        <div ref={containerRef} className="relative w-full">
            <div className="relative">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => {
                        setQuery(e.target.value)
                        setIsOpen(true)
                    }}
                    onFocus={() => setIsOpen(true)}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pl-4 pr-10 text-xs text-slate-800 placeholder-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition"
                />
                {query ? (
                    <button
                        type="button"
                        onClick={() => {
                            setQuery('')
                            setIsOpen(false)
                        }}
                        className="absolute right-10 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 focus:outline-none"
                    >
                        <X className="h-3 w-3" />
                    </button>
                ) : null}
                <Search className="absolute right-3.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
            </div>

            {showDropdown && (
                <div className="absolute left-0 right-0 mt-2 z-50 max-h-80 overflow-y-auto rounded-xl border border-slate-200 bg-white p-2 shadow-xl">
                    {isLoading ? (
                        <div className="p-3 text-center text-xs text-slate-400">Đang tìm kiếm...</div>
                    ) : subjects.length === 0 ? (
                        <div className="p-3 text-center text-xs text-slate-400">Không tìm thấy môn học phù hợp</div>
                    ) : (
                        <ul className="space-y-0.5">
                            {subjects.map((subject, index) => {
                                const isSelected = index === activeIndex
                                const firstMajorName = subject.majors && subject.majors.length > 0 ? subject.majors[0].name : 'N/A'
                                return (
                                    <li
                                        key={subject.id}
                                        onClick={() => handleSelect(subject)}
                                        className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition ${isSelected ? 'bg-indigo-50/60 text-indigo-900' : 'text-slate-700 hover:bg-indigo-50/60'
                                            }`}
                                    >
                                        <BookOpen className="h-4 w-4 shrink-0 text-slate-400" />
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2">
                                                <span className="font-mono text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded-sm shrink-0">
                                                    {subject.code}
                                                </span>
                                                <span className="text-xs truncate">
                                                    {highlightMatch(subject.name, debouncedQuery)}
                                                </span>
                                            </div>
                                            <div className="text-[10px] text-slate-400 mt-0.5 truncate">
                                                {firstMajorName}
                                            </div>
                                        </div>
                                    </li>
                                )
                            })}
                        </ul>
                    )}
                </div>
            )}
        </div>
    )
}
