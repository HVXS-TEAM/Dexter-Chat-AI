import type { CSSProperties } from 'react'
import { useNavigate } from 'react-router-dom'
import { enableGuestMode, useAuth } from '../auth'
import MagicRings from './MagicRings'

const baseButtonStyle: CSSProperties = {
  fontWeight: 600,
  fontSize: '15px',
  padding: '13px 34px',
  borderRadius: '999px',
  cursor: 'pointer',
  transition: 'transform 0.15s ease, box-shadow 0.15s ease',
}

/** Bouton principal : style du bouton unique de la maquette `DexterWelcome.jsx`. */
const primaryButtonStyle: CSSProperties = {
  ...baseButtonStyle,
  background: 'var(--text-primary)',
  color: 'var(--background)',
  border: 'none',
  boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
}

/** Bouton secondaire : style des controles deja utilises dans l'app (Login, cartes Accueil). */
const secondaryButtonStyle: CSSProperties = {
  ...baseButtonStyle,
  background: 'var(--surface-secondary)',
  color: 'var(--text-primary)',
  border: '1px solid var(--border-default)',
}

/** Effet de survol du bouton principal : comportement d'origine de la maquette `DexterWelcome.jsx`. */
function highlightPrimaryButton(button: HTMLButtonElement, isActive: boolean): void {
  button.style.transform = isActive ? 'scale(1.03)' : 'scale(1)'
  button.style.boxShadow = isActive ? '0 10px 28px rgba(0,0,0,0.25)' : '0 8px 20px rgba(0,0,0,0.15)'
}

/** Effet de survol du bouton secondaire : mise a l'echelle seule (il n'a pas d'ombre propre). */
function highlightSecondaryButton(button: HTMLButtonElement, isActive: boolean): void {
  button.style.transform = isActive ? 'scale(1.03)' : 'scale(1)'
}

export default function DexterWelcome() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  const handleContinue = () => {
    navigate('/chat')
  }

  const handleLogin = () => {
    navigate('/login')
  }

  const handleGuestStart = () => {
    enableGuestMode()
    navigate('/')
  }

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        minHeight: '640px',
        borderRadius: '20px',
        overflow: 'hidden',
        background: 'radial-gradient(120% 140% at 50% 0%, var(--surface-secondary) 0%, var(--background) 46%, var(--surface-container) 100%)',
        fontFamily: "var(--font-family)",
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* halo animé en arrière-plan */}
      <MagicRings
        color="#5B8DEF"
        colorTwo="#9B6DFF"
        speed={0.6}
        ringCount={5}
        attenuation={9}
        lineThickness={1.4}
        baseRadius={0.22}
        radiusStep={0.09}
        scaleRate={0.12}
        opacity={0.55}
        followMouse
        mouseInfluence={0.12}
        hoverScale={1.05}
        parallax={0.03}
        alphaMode="luminance"
      />

      {/* voile de contraste pour garder le texte lisible */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(60% 50% at 50% 42%, rgba(0,0,0,0.05) 0%, rgba(0,0,0,0.35) 65%, rgba(0,0,0,0.65) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* badge plan */}
      <div
        style={{
          position: 'absolute',
          top: '24px',
          right: '24px',
          background: 'var(--text-primary)',
          color: 'var(--background)',
          fontWeight: 700,
          fontSize: '13px',
          padding: '7px 16px',
          borderRadius: '999px',
          letterSpacing: '0.01em',
          zIndex: 3,
        }}
      >
        Free
      </div>

      {/* contenu central */}
      <div
        style={{
          position: 'relative',
          zIndex: 2,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          padding: '32px',
          maxWidth: '420px',
        }}
      >
        <div
          style={{
            width: '76px',
            height: '76px',
            borderRadius: '22px',
            background: 'var(--surface)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '28px',
            boxShadow: '0 0 0 1px var(--border-default), 0 12px 30px rgba(79, 70, 229, 0.25)',
          }}
        >
          <img
            src="/DexterIcons.ico"
            alt="Logo Dexter"
            width="52"
            height="52"
            style={{ objectFit: 'contain' }}
          />
        </div>

        <h1
          style={{
            color: 'var(--text-primary)',
            fontSize: '34px',
            fontWeight: 600,
            margin: 0,
            letterSpacing: '-0.01em',
          }}
        >
          Dexter
        </h1>

        <p
          style={{
            color: 'var(--text-secondary)',
            fontSize: '15px',
            marginTop: '10px',
            marginBottom: '32px',
            lineHeight: 1.5,
          }}
        >
          Ton assistant pour la compta, la finance et plus encore
        </p>

        {isAuthenticated ? (
          <button
            onClick={handleContinue}
            style={primaryButtonStyle}
            onMouseEnter={(event) => highlightPrimaryButton(event.currentTarget, true)}
            onMouseLeave={(event) => highlightPrimaryButton(event.currentTarget, false)}
          >
            Continuer
          </button>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', maxWidth: '280px' }}>
            <button
              onClick={handleLogin}
              style={primaryButtonStyle}
              onMouseEnter={(event) => highlightPrimaryButton(event.currentTarget, true)}
              onMouseLeave={(event) => highlightPrimaryButton(event.currentTarget, false)}
            >
              Se connecter
            </button>
            <button
              onClick={handleGuestStart}
              style={secondaryButtonStyle}
              onMouseEnter={(event) => highlightSecondaryButton(event.currentTarget, true)}
              onMouseLeave={(event) => highlightSecondaryButton(event.currentTarget, false)}
            >
              Essayer sans connexion
            </button>
          </div>
        )}
      </div>

      {/* copyright */}
      <div
        style={{
          position: 'absolute',
          bottom: '20px',
          left: 0,
          right: 0,
          textAlign: 'center',
          color: 'var(--text-secondary)',
          fontSize: '12px',
          opacity: 0.45,
          zIndex: 3,
        }}
      >
        © 2026 Dexter. Tous droits réservés.
      </div>
    </div>
  )
}
