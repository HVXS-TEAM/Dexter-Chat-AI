import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Accueil from './pages/Accueil'
import Chat from './pages/Chat'
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
            <Route
              element={
                <ProtectedRoute>
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
              <Route path="/profil" element={<Profil />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}
