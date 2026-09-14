import { useParams } from 'react-router-dom'

export default function Matiere() {
  const { id } = useParams<{ id: string }>()
  const title = id ? `Matière ${id}` : 'Détail matière'

  return (
    <section className="placeholder-page" aria-labelledby="page-title">
      <h1 id="page-title">{title}</h1>
      <p>Le détail de cette matière sera disponible prochainement.</p>
    </section>
  )
}
