import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Accueil from './pages/Accueil'
import Chat from './pages/Chat'
import Historique from './pages/Historique'
import Matiere from './pages/Matiere'
import Matieres from './pages/Matieres'
import Profil from './pages/Profil'
import Recherche from './pages/Recherche'
import { ThemeProvider } from './theme/ThemeProvider'

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Accueil />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/recherche" element={<Recherche />} />
            <Route path="/matiere/:id" element={<Matiere />} />
            <Route path="/matieres" element={<Matieres />} />
            <Route path="/historique" element={<Historique />} />
            <Route path="/profil" element={<Profil />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}
