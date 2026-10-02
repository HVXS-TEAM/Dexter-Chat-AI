import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import DexterWelcome from './components/DexterWelcome'
import Layout from './components/Layout'
import Accueil from './pages/Accueil'
import Chat from './pages/Chat'
import Classes from './pages/Classes'
import Historique from './pages/Historique'
import Login from './pages/Login'
import Matiere from './pages/Matiere'
import Matieres from './pages/Matieres'
import Profil from './pages/Profil'
import Recherche from './pages/Recherche'
import Register from './pages/Register'
import { AuthProvider, ProtectedRoute } from './auth'
import { ThemeProvider } from './theme/ThemeProvider'

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            {/* Ecran d'ouverture public : connexion ou essai sans connexion */}
            <Route path="/bienvenue" element={<DexterWelcome />} />
            {/* Espace consultable sans compte (essai sans connexion) */}
            <Route
              element={
                <ProtectedRoute allowGuest redirectTo="/bienvenue">
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<Accueil />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/recherche" element={<Recherche />} />
              <Route path="/matiere/:id" element={<Matiere />} />
              <Route path="/matieres" element={<Matieres />} />
              <Route path="/historique" element={<Historique />} />
            </Route>

            {/* Espace personnel : compte requis */}
            <Route
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route path="/profil" element={<Profil />} />
              <Route path="/classes" element={<Classes />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}
