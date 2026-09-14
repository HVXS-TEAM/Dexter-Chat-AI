import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

type Theme = 'dark' | 'light'

type ThemeContextValue = {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined)
const storageKey = 'dexter-theme'

function getThemeFromTime(): Theme {
  const hour = new Date().getHours()
  // Jour : 6h-18h → clair, Nuit : 18h-6h → sombre
  return hour >= 6 && hour < 18 ? 'light' : 'dark'
}

function getInitialTheme(): Theme {
  const storedTheme = window.localStorage.getItem(storageKey)
  if (storedTheme === 'dark' || storedTheme === 'light') {
    return storedTheme
  }
  // Pas de préférence → thème basé sur l'heure
  return getThemeFromTime()
}

type ThemeProviderProps = {
  children: ReactNode
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    window.localStorage.setItem(storageKey, theme)
  }, [theme])

  function setTheme(newTheme: Theme) {
    setThemeState(newTheme)
  }

  function toggleTheme() {
    setThemeState((currentTheme) => (currentTheme === 'dark' ? 'light' : 'dark'))
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext)

  if (!context) {
    throw new Error('useTheme must be used inside ThemeProvider')
  }

  return context
}
