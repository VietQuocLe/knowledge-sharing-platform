import { useState } from 'react'

export function useSidebar() {
    const [isCollapsed, setIsCollapsedState] = useState<boolean>(() => {
        try {
            const stored = localStorage.getItem('vault_sidebar_collapsed')
            return stored ? JSON.parse(stored) === true : false
        } catch {
            return false
        }
    })

    const setIsCollapsed = (collapsed: boolean) => {
        setIsCollapsedState(collapsed)
        try {
            localStorage.setItem('vault_sidebar_collapsed', JSON.stringify(collapsed))
        } catch (e) {
            console.error('Error saving sidebar collapsed state', e)
        }
    }

    return {
        isCollapsed,
        setIsCollapsed,
    }
}
