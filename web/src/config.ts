// Site/author configuration. Fill these in before publishing (see PUBLISHING.md).
// No analytics, trackers or third-party calls are configured anywhere in this app.
export interface SiteConfig {
  authorName: string;
  authorTitle: string;
  authorBio: string;
  authorEmail: string;
  authorLinkedIn: string;
  authorGitHub: string;
  companyName: string;
  companyUrl: string;
  logoPath: string;
  repoUrl: string;
}

export const CONFIG: SiteConfig = {
  authorName: "Celso Zanchetta Junior",
  authorTitle: "Engenheiro civil — infraestrutura de transportes; mestre em Saúde Ambiental",
  authorBio: "",
  authorEmail: "celso.zanchetta@vortexinfra.com",
  authorLinkedIn: "https://www.linkedin.com/in/celsozanchetta/",
  authorGitHub: "https://github.com/czanchetta",
  companyName: "",
  companyUrl: "",
  logoPath: "./logo.svg",
  repoUrl: "https://github.com/czanchetta/urban-tree-geometry",
};
