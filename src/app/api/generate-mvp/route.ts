import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { opportunityId } = body

    // Fetch the opportunity details
    const opportunity = await db.opportunity.findUnique({
      where: { id: opportunityId },
      include: { globalStartup: true }
    })

    if (!opportunity) {
      return NextResponse.json(
        { error: 'Opportunity not found' },
        { status: 404 }
      )
    }

    // Generate MVP roadmap using AI
    const roadmap = await generateMVPRoadmapWithAI(opportunity)

    // Save the roadmap to the database
    const savedRoadmap = await db.mVPRoadmap.create({
      data: {
        opportunityId: opportunity.id,
        title: roadmap.title,
        targetMarket: roadmap.targetMarket,
        pricingStrategy: roadmap.pricingStrategy,
        channels: JSON.stringify(roadmap.channels),
        techStack: JSON.stringify(roadmap.techStack),
        milestones: JSON.stringify(roadmap.milestones),
        timeline: roadmap.timeline
      }
    })

    return NextResponse.json({
      success: true,
      roadmap: savedRoadmap,
      generated: roadmap
    })
  } catch (error) {
    console.error('Error generating MVP roadmap:', error)
    return NextResponse.json(
      { error: 'Failed to generate MVP roadmap' },
      { status: 500 }
    )
  }
}

// AI-powered MVP roadmap generation
async function generateMVPRoadmapWithAI(opportunity: any) {
  // In production, this would use the LLM SDK from z-ai-web-dev-sdk
  // For now, we'll generate based on the opportunity details

  const isB2B = opportunity.description.toLowerCase().includes('b2b') ||
                opportunity.globalSource?.toLowerCase().includes('saas')

  const isConsumer = opportunity.description.toLowerCase().includes('consumer') ||
                     opportunity.description.toLowerCase().includes('b2c')

  // Generate title
  const title = `MVP Roadmap: ${opportunity.title} (India)`

  // Generate target market
  const targetMarket = generateTargetMarket(opportunity)

  // Generate pricing strategy
  const pricingStrategy = generatePricingStrategy(opportunity, isB2B, isConsumer)

  // Generate channels
  const channels = generateChannels(opportunity, isB2B, isConsumer)

  // Generate tech stack
  const techStack = generateTechStack(opportunity, isB2B, isConsumer)

  // Generate milestones
  const milestones = generateMilestones(opportunity, isB2B, isConsumer)

  // Generate timeline
  const timeline = generateTimeline(opportunity)

  return {
    title,
    targetMarket,
    pricingStrategy,
    channels,
    techStack,
    milestones,
    timeline
  }
}

function generateTargetMarket(opportunity: any): string {
  const desc = opportunity.description.toLowerCase()

  if (desc.includes('b2b') || desc.includes('saas') || desc.includes('business')) {
    return `Primary: Indian SMEs and startups in Tier 1 cities (Mumbai, Delhi NCR, Bangalore, Hyderabad, Chennai)\n\n` +
           `Secondary: Large enterprises looking for specialized solutions\n\n` +
           `Market Size: ~5M registered businesses, growing at 12% annually\n\n` +
           `Focus on businesses with 10-100 employees initially`
  }

  if (desc.includes('education') || desc.includes('learning') || desc.includes('student')) {
    return `Primary: Students preparing for competitive exams (JEE, NEET, UPSC, CAT)\n\n` +
           `Secondary: Working professionals seeking skill development\n\n` +
           `Geographic Focus: Start with South India (Tamil Nadu, Karnataka, Andhra Pradesh)\n\n` +
           `Market Size: ~37M students in higher education`
  }

  if (desc.includes('fintech') || desc.includes('finance') || desc.includes('payment')) {
    return `Primary: Tech-savvy millennials and Gen Z in urban areas\n\n` +
           `Secondary: Small business owners and freelancers\n\n` +
           `Geographic Focus: Metro cities first, expand to Tier 2 cities\n\n` +
           `Market Size: ~190M digitally active users`
  }

  return `Primary: Urban professionals and students in Tier 1 cities\n\n` +
         `Secondary: Aspiring users in Tier 2 and Tier 3 cities\n\n` +
         `Market Size: ~250M smartphone users in target demographic\n\n` +
         `Focus on English speakers initially, expand to regional languages`
}

function generatePricingStrategy(opportunity: any, isB2B: boolean, isConsumer: boolean): string {
  if (isB2B) {
    return `**Tiered Pricing Model (INR)**\n\n` +
           `• Starter: ₹999/month - Up to 5 users\n` +
           `• Professional: ₹2,999/month - Up to 20 users\n` +
           `• Enterprise: Custom pricing - Unlimited users\n\n` +
           `**Payment Gateway**: Razorpay (recommended)\n` +
           `**Invoicing**: Provide GST invoices for business customers\n` +
           `**Annual Discount**: 20% off on yearly plans\n\n` +
           `**Free Trial**: 14-day trial with full access\n` +
           `**Proof of Concept**: Custom demo for enterprise clients`
  }

  if (isConsumer) {
    return `**Freemium Model**\n\n` +
           `• Free: Basic features with ads\n` +
           `• Premium: ₹99/month - Ad-free + additional features\n\n` +
           `**Payment Methods**:\n` +
           `• UPI (Google Pay, PhonePe, Paytm)\n` +
           `• Credit/Debit Cards\n` +
           `• Netbanking\n\n` +
           `**Pricing Psychology**:\n` +
           `• Use charm pricing (₹99 instead of ₹100)\n` +
           `• Annual plan at ₹999 (17% discount)\n` +
           `• Student discount: 50% off with ID verification`
  }

  return `**Value-Based Pricing**\n\n` +
         `• Basic: Free for individual users\n` +
         `• Pro: ₹199/month - Enhanced features\n` +
         `• Team: ₹599/month - For teams up to 5\n\n` +
         `**Payment Integration**: Razorpay or PayU\n` +
         `**Localized Pricing**: Adjust for regional purchasing power\n` +
         `**Promotional Offers**: Launch discounts to drive adoption`
}

function generateChannels(opportunity: any, isB2B: boolean, isConsumer: boolean): string[] {
  if (isB2B) {
    return [
      { channel: 'LinkedIn', strategy: 'Targeted ads and content marketing to decision makers' },
      { channel: 'Cold Outreach', strategy: 'Personalized emails to SMEs using Apollo or similar tools' },
      { channel: 'Partnerships', strategy: 'Integrate with existing business tools (Zoho, Tally)' },
      { channel: 'Webinars', strategy: 'Educational webinars on industry pain points' },
      { channel: 'Referral Program', strategy: 'Offer discounts for customer referrals' },
      { channel: 'Industry Events', strategy: 'Speak at tech conferences and startup meetups' }
    ]
  }

  if (isConsumer) {
    return [
      { channel: 'Social Media', strategy: 'Instagram and YouTube content marketing' },
      { channel: 'Influencer Marketing', strategy: 'Partner with micro-influencers in relevant niches' },
      { channel: 'WhatsApp Marketing', strategy: 'Broadcast lists for updates and promotions' },
      { channel: 'ASO', strategy: 'Optimize app store listings for organic discovery' },
      { channel: 'PR', strategy: 'Tech media coverage (YourStory, Inc42, Entrackr)' },
      { channel: 'Referral Program', strategy: 'In-app referrals with cashback or premium time' }
    ]
  }

  return [
    { channel: 'Content Marketing', strategy: 'Blog posts and SEO to drive organic traffic' },
    { channel: 'Social Media', strategy: 'LinkedIn for B2B, Instagram/YouTube for B2C' },
    { channel: 'WhatsApp Business', strategy: 'Direct engagement and customer support' },
    { channel: 'Community Building', strategy: 'Discord/Slack communities for power users' },
    { channel: 'PR', strategy: 'Launch coverage in tech media' }
  ]
}

function generateTechStack(opportunity: any, isB2B: boolean, isConsumer: boolean): string[] {
  const baseStack = [
    { layer: 'Frontend', tech: 'Next.js 15 + React 18 + TypeScript' },
    { layer: 'Styling', tech: 'Tailwind CSS + shadcn/ui' },
    { layer: 'Database', tech: 'PostgreSQL (or SQLite for MVP)' },
    { layer: 'ORM', tech: 'Prisma' },
    { layer: 'Authentication', tech: 'NextAuth.js v4' },
    { layer: 'API', tech: 'Next.js API Routes + tRPC' },
    { layer: 'Deployment', tech: 'Vercel (frontend) + Railway/Render (backend)' }
  ]

  if (isB2B) {
    return [
      ...baseStack,
      { layer: 'Payment Gateway', tech: 'Razorpay' },
      { layer: 'Analytics', tech: 'PostHog or Amplitude' },
      { layer: 'Email', tech: 'SendGrid or AWS SES' },
      { layer: 'CRM', tech: 'HubSpot or custom build' },
      { layer: 'Support', tech: 'Intercom or Freshdesk' }
    ]
  }

  if (isConsumer) {
    return [
      ...baseStack,
      { layer: 'Payment Gateway', tech: 'Razorpay (UPI integration)' },
      { layer: 'Push Notifications', tech: 'OneSignal' },
      { layer: 'Analytics', tech: 'Mixpanel' },
      { layer: 'A/B Testing', tech: 'VWO or Statsig' },
      { layer: 'Support', tech: 'WhatsApp Business API' }
    ]
  }

  return baseStack
}

function generateMilestones(opportunity: any, isB2B: boolean, isConsumer: boolean): string[] {
  if (isB2B) {
    return [
      {
        phase: 'Phase 1: MVP Development (Weeks 1-4)',
        tasks: [
          'Core functionality implementation',
          'User authentication and onboarding',
          'Payment integration with Razorpay',
          'Basic dashboard for users',
          'Admin panel for content management'
        ]
      },
      {
        phase: 'Phase 2: Beta Launch (Weeks 5-8)',
        tasks: [
          'Onboard 10-20 beta customers',
          'Collect feedback and iterate',
          'Fix critical bugs',
          'Optimize performance',
          'Create documentation and help center'
        ]
      },
      {
        phase: 'Phase 3: Public Launch (Weeks 9-12)',
        tasks: [
          'Launch on Product Hunt',
          'Content marketing campaign',
          'Cold outreach to 100+ prospects',
          'Webinar series for lead generation',
          'Implement referral program'
        ]
      },
      {
        phase: 'Phase 4: Growth & Scale (Months 4-6)',
        tasks: [
          'Reach 50 paying customers',
          'Hire first salesperson',
          'Develop advanced features',
          'Expand to new customer segments',
          'Build integrations with popular tools'
        ]
      }
    ]
  }

  if (isConsumer) {
    return [
      {
        phase: 'Phase 1: MVP Development (Weeks 1-4)',
        tasks: [
          'Core functionality implementation',
          'Social login (Google, Facebook)',
          'UI/UX polish',
          'Payment integration (Razorpay)',
          'Push notification setup'
        ]
      },
      {
        phase: 'Phase 2: Soft Launch (Weeks 5-8)',
        tasks: [
          'Launch on Google Play Store',
          'Onboard 100 beta users',
          'Gather user feedback',
          'Optimize onboarding flow',
          'Fix critical bugs'
        ]
      },
      {
        phase: 'Phase 3: Public Launch (Weeks 9-12)',
        tasks: [
          'Launch on Apple App Store',
          'Influencer marketing campaign',
          'Social media push',
          'ASO optimization',
          'Launch referral program'
        ]
      },
      {
        phase: 'Phase 4: Growth & Scale (Months 4-6)',
        tasks: [
          'Reach 10,000 app installs',
          'Optimize user retention',
          'Add premium features',
          'Launch affiliate program',
          'Expand to regional languages'
        ]
      }
    ]
  }

  return [
    {
      phase: 'Phase 1: Foundation (Weeks 1-4)',
      tasks: [
        'Core feature development',
        'User authentication',
        'Basic UI implementation',
        'Database setup and optimization'
      ]
    },
    {
      phase: 'Phase 2: Beta (Weeks 5-8)',
      tasks: [
        'Beta testing with 50 users',
        'Feedback collection',
        'Bug fixes and iterations',
        'Performance optimization'
      ]
    },
    {
      phase: 'Phase 3: Launch (Weeks 9-12)',
      tasks: [
        'Public launch',
        'Marketing campaign',
        'Customer support setup',
        'Analytics implementation'
      ]
    }
  ]
}

function generateTimeline(opportunity: any): string {
  return `**Total Timeline: 12 weeks to MVP launch**\n\n` +
         `**Weeks 1-4:** Core development - Build MVP features\n` +
         `**Weeks 5-6:** Testing & QA - Internal testing and bug fixes\n` +
         `**Weeks 7-8:** Beta launch - Test with limited users\n` +
         `**Weeks 9-10:** Iteration - Refine based on feedback\n` +
         `**Weeks 11-12:** Public launch - Go-to-market execution\n\n` +
         `**Post-Launch (Months 4-6):** Growth phase - Scale operations and expand features`
}
