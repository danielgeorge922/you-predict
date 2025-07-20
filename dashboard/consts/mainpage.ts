const whyReasonSections = [
  {
    title: "Intelligent CDN Provisioning",
    description:
      "Automatically allocate content delivery resources based on predicted viral potential. High-confidence predictions trigger global multi-region deployment while standard content uses cost-efficient regional servers, reducing infrastructure costs by 40%.",
    graphic: "/images/CDN.jpg",
  },
  {
    title: "Proactive Content Promotion",
    description:
      "Surface high-potential videos in recommendation algorithms before engagement data is available. Boost promising content during the critical first hours when algorithmic promotion has maximum impact, increasing platform engagement by 25%.",
    graphic: "/images/content-promotion.png",
  },
  {
    title: "MLOps Model Monitoring",
    description:
      "Continuous accuracy tracking with automated drift detection and retraining pipelines. Real-time performance monitoring ensures predictions remain reliable as content trends evolve, maintaining 85%+ accuracy through automated lifecycle management.",
    graphic: "/images/mlops-monitoring.png",
  },
];

const techStack = [
  { 
    name: "Docker", 
    icon: "/icons/docker.svg",
    description: "Containerized the entire ML pipeline and web application for consistent deployment across environments. Docker containers ensure reproducible builds and simplified scaling on cloud infrastructure."
  },
  { 
    name: "GCP", 
    icon: "/icons/gcp.svg",
    description: "Google Cloud Platform hosts the entire infrastructure including automated data collection VMs, Cloud Run for serverless API deployment, and BigQuery for data warehousing. Provides scalable compute and storage resources."
  },
  { 
    name: "Next.js", 
    icon: "/icons/next.svg",
    description: "React framework powering the dashboard frontend with server-side rendering for optimal performance. Handles real-time data visualization and interactive charts for model predictions and metrics."
  },
  { 
    name: "Python", 
    icon: "/icons/python.svg",
    description: "Core language for the machine learning pipeline including data preprocessing, feature engineering, model training with XGBoost, and API development using FastAPI for prediction endpoints."
  },
  { 
    name: "Tailwind", 
    icon: "/icons/tailwind.svg",
    description: "Utility-first CSS framework for rapid UI development. Ensures consistent design system across the dashboard with responsive layouts and custom data visualization components."
  },
  { 
    name: "TypeScript", 
    icon: "/icons/typescript.svg",
    description: "Provides type safety across the entire frontend codebase, reducing runtime errors and improving developer experience. Ensures reliable data flow between API responses and UI components."
  },
  { 
    name: "Vercel", 
    icon: "/icons/vercel.svg",
    description: "Deployment platform for the Next.js frontend with automatic CI/CD pipeline. Provides global edge deployment for fast loading times and seamless integration with GitHub for continuous deployment."
  },
];

export { whyReasonSections, techStack };