const STEPS = [
  {
    title: "Choisissez une fonctionnalité",
    text: "Dans la colonne de gauche : liste de pièces, rapport, soumission…",
  },
  {
    title: "Indiquez les fichiers",
    text: "Cliquez sur « Parcourir » ou glissez-déposez vos plans, dossiers et modèles directement sur le champ.",
  },
  {
    title: "Lancez le traitement",
    text: "La barre de progression avance fichier par fichier. Vous pouvez annuler à tout moment.",
  },
  {
    title: "Récupérez le résultat",
    text: "Les fichiers produits sont écrits dans le dossier de sortie. Vos fichiers d'origine ne sont jamais modifiés.",
  },
];

export function WelcomeView() {
  return (
    <section className="welcome">
      <header>
        <h1>Comment ça marche</h1>
        <p className="muted">
          Drawflow automatise la production de listes de pièces, de rapports et de soumissions à
          partir de vos plans.
        </p>
      </header>
      <ol className="welcome-steps">
        {STEPS.map((step) => (
          <li key={step.title}>
            <strong>{step.title}</strong>
            <span className="muted">{step.text}</span>
          </li>
        ))}
      </ol>
      <p className="muted">
        En cas de problème, un message indique le fichier concerné et quoi faire. Le détail complet
        reste disponible dans le journal. L'état du moteur et la version sont affichés dans la barre
        du bas.
      </p>
    </section>
  );
}
