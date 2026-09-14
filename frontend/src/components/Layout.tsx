import { Link, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../auth'
import { useTheme } from '../theme/ThemeProvider'

type NavigationItem = {
  label: string
  to: string
  icon: string
  end?: boolean
  section?: 'profile' | 'settings'
}

const navigationItems: NavigationItem[] = [
  { label: 'Accueil', to: '/', icon: 'home', end: true },
  { label: 'Recherche', to: '/recherche', icon: 'search' },
  { label: 'Chat', to: '/chat', icon: 'chat' },
  { label: 'Mes matières', to: '/matieres', icon: 'auto_stories' },
  { label: 'Historique', to: '/historique', icon: 'history' },
  { label: 'Profil', to: '/profil', icon: 'account_circle', section: 'profile' },
  { label: 'Paramètres', to: '/profil#parametres', icon: 'settings', section: 'settings' },
]

function NavigationLink({ item }: { item: NavigationItem }) {
  const location = useLocation()
  const isSectionActive =
    item.section === 'settings'
      ? location.hash === '#parametres'
      : item.section === 'profile'
        ? location.pathname === '/profil' && location.hash !== '#parametres'
        : item.end
          ? location.pathname === item.to
          : location.pathname.startsWith(item.to)

  return (
    <Link
      to={item.to}
      aria-current={isSectionActive ? 'page' : undefined}
      className={`navigation-link${isSectionActive ? ' navigation-link-active' : ''}`}
    >
      <span className="material-symbols-outlined" aria-hidden="true">
        {item.icon}
      </span>
      <span className="navigation-label">{item.label}</span>
    </Link>
  )
}

export default function Layout() {
  const { theme, toggleTheme } = useTheme()
  const { user, isAuthenticated, logout } = useAuth()
  const themeIcon = theme === 'dark' ? 'light_mode' : 'dark_mode'
  const themeLabel = theme === 'dark' ? 'Activer le thème clair' : 'Activer le thème sombre'

  const userInitials = user
    ? user.email.slice(0, 2).toUpperCase()
    : ''

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <img className="brand-mark" src="/DexterIcons.ico" alt="Dexter" />
          <div className="brand-copy">
            <span className="brand-name">Dexter</span>
            <span className="brand-subtitle">AI Study Assistant</span>
          </div>
        </div>

        <nav className="primary-navigation" aria-label="Navigation principale">
          {navigationItems.map((item) => (
            <NavigationLink key={`${item.label}-${item.to}`} item={item} />
          ))}
        </nav>

        <div className="sidebar-footer">
          {isAuthenticated ? (
            <div className="user-block">
              <div className="user-avatar" aria-label="Avatar utilisateur">
                {userInitials}
              </div>
              <div className="user-info">
                <span className="user-email">{user?.email}</span>
                <button className="logout-button" type="button" onClick={logout} aria-label="Se déconnecter">
                  <span className="material-symbols-outlined" aria-hidden="true">logout</span>
                  <span>Déconnexion</span>
                </button>
              </div>
            </div>
          ) : (
            <Link className="login-button" to="/login">
              <span className="material-symbols-outlined" aria-hidden="true">login</span>
              <span>Se connecter</span>
            </Link>
          )}
          <button className="upgrade-button" type="button" aria-disabled="true" disabled>
            Upgrade to Pro
          </button>
          <button className="theme-toggle" type="button" onClick={toggleTheme} aria-label={themeLabel}>
            <span className="material-symbols-outlined" aria-hidden="true">
              {themeIcon}
            </span>
            <span className="theme-toggle-label">Thème</span>
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
