import Link from "next/link"

const sections = [
  {
    title: "Using Vortex",
    paragraphs: [
      "These terms apply when you access or use the Vortex website and services. By using Vortex, you agree to follow these terms. If you use Vortex for an organization, you confirm that you are allowed to accept these terms for that organization.",
    ],
  },
  {
    title: "Your account and API keys",
    paragraphs: [
      "You are responsible for keeping your account credentials and API keys secure, and for activity carried out through them. Tell your organization administrator promptly if you believe an account or key has been used without permission.",
      "Provide accurate account information and use only accounts and workspaces you are authorized to access.",
    ],
  },
  {
    title: "Acceptable use",
    paragraphs: [
      "Do not use Vortex to break the law, violate another person’s rights, gain unauthorized access, interfere with the service, or send malicious code. Do not attempt to bypass service limits or security controls.",
    ],
  },
  {
    title: "Data you submit",
    paragraphs: [
      "You keep your rights to the information you submit. You give Vortex permission to process that information only as needed to operate and provide the service to you.",
      "You are responsible for having the rights and permissions needed to submit your data, including event data and personal information. Do not send sensitive information unless your organization has confirmed that the service is appropriate for it.",
    ],
  },
  {
    title: "Service and third-party providers",
    paragraphs: [
      "Vortex may depend on hosting, networking, and other third-party services. The service may occasionally be unavailable or change as it is maintained and improved. We may suspend access when needed to protect the service, its users, or its infrastructure.",
    ],
  },
  {
    title: "Ownership",
    paragraphs: [
      "Vortex and its software, branding, and website are owned by their respective rights holders. These terms give you permission to use the service; they do not transfer ownership of Vortex to you.",
    ],
  },
  {
    title: "Ending or changing access",
    paragraphs: [
      "You may stop using Vortex at any time. An organization administrator may manage your workspace access. We may update these terms as the service changes; continued use after an update means you accept the revised terms.",
    ],
  },
  {
    title: "Disclaimers and liability",
    paragraphs: [
      "Vortex is provided as available. To the extent permitted by applicable law, the service is provided without warranties, and Vortex is not liable for indirect or consequential losses arising from your use of it.",
    ],
  },
]

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-black px-5 py-12 text-white sm:px-8 sm:py-16">
      <div className="mx-auto max-w-3xl">
        <Link href="/" className="font-syne text-xl font-bold tracking-tight text-white">
          Vortex
        </Link>

        <header className="mb-10 mt-12 border-b border-[var(--color-border)] pb-8">
          <p className="mb-3 font-dm text-xs uppercase tracking-[0.2em] text-brand">
            Vortex service terms
          </p>
          <h1 className="font-syne text-3xl font-bold sm:text-4xl">Terms and Conditions</h1>
          <p className="mt-4 font-dm text-sm text-white/45">Effective date: October 24, 2026</p>
        </header>

        <div className="space-y-8">
          {sections.map((section, index) => (
            <section key={section.title} className="space-y-3">
              <h2 className="font-syne text-lg font-semibold text-white">
                <span className="mr-3 font-dm text-xs text-brand">
                  {String(index + 1).padStart(2, "0")}
                </span>
                {section.title}
              </h2>
              {section.paragraphs.map((paragraph) => (
                <p key={paragraph} className="font-dm text-sm leading-7 text-white/60">
                  {paragraph}
                </p>
              ))}
            </section>
          ))}
        </div>

        <div className="mt-12 border-t border-[var(--color-border)] pt-6">
          <Link href="/" className="font-dm text-sm text-brand transition-colors hover:text-white">
            ← Back to Vortex
          </Link>
        </div>
      </div>
    </main>
  )
}
