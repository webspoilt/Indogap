import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
    console.log('🌱 Seeding database...')

    // Clear existing data
    await prisma.roadmap.deleteMany()
    await prisma.opportunity.deleteMany()
    await prisma.indianStartup.deleteMany()

    // Create Indian Startups
    const startups = await Promise.all([
        prisma.indianStartup.create({
            data: {
                name: 'Razorpay',
                description: 'Payment gateway and financial services platform for businesses in India',
                category: 'Fintech',
                website: 'https://razorpay.com'
            }
        }),
        prisma.indianStartup.create({
            data: {
                name: 'Swiggy',
                description: 'Food delivery and quick commerce platform',
                category: 'Food Delivery',
                website: 'https://swiggy.com'
            }
        }),
        prisma.indianStartup.create({
            data: {
                name: 'Zerodha',
                description: 'Discount stock broker and trading platform',
                category: 'Fintech',
                website: 'https://zerodha.com'
            }
        }),
        prisma.indianStartup.create({
            data: {
                name: 'CRED',
                description: 'Credit card payments and rewards platform',
                category: 'Fintech',
                website: 'https://cred.club'
            }
        }),
        prisma.indianStartup.create({
            data: {
                name: 'Meesho',
                description: 'Social commerce platform for small businesses',
                category: 'E-commerce',
                website: 'https://meesho.com'
            }
        }),
        prisma.indianStartup.create({
            data: {
                name: 'PhonePe',
                description: 'Digital payments and UPI platform',
                category: 'Fintech',
                website: 'https://phonepe.com'
            }
        }),
        prisma.indianStartup.create({
            data: {
                name: 'Urban Company',
                description: 'Home services marketplace',
                category: 'Services',
                website: 'https://urbancompany.com'
            }
        }),
        prisma.indianStartup.create({
            data: {
                name: 'Dunzo',
                description: 'Quick commerce and delivery platform',
                category: 'Logistics',
                website: 'https://dunzo.com'
            }
        })
    ])

    console.log(`✅ Created ${startups.length} Indian startups`)

    // Create Opportunities
    const opportunities = await Promise.all([
        prisma.opportunity.create({
            data: {
                title: 'AI-Powered Legal Document Review',
                description: 'Automated legal document analysis using AI. Huge potential in India where legal processes are slow and expensive.',
                globalSource: 'YC',
                globalReference: 'Harvey AI (W23)',
                successScore: 85,
                status: 'New',
                indianCompetitors: 'SpotDraft (contract management), LegalKart (basic legal services)',
                gapAnalysis: 'No direct competitor doing AI-powered document review for Indian legal system. Major gap exists.',
                culturalFit: 75,
                logisticsComplexity: 25,
                paymentReadiness: 80,
                timingAlignment: 90,
                monopolyPotential: 70,
                regulatoryRisk: 40,
                executionFeasibility: 80
            }
        }),
        prisma.opportunity.create({
            data: {
                title: 'Vertical SaaS for Indian SMB Accounting',
                description: 'AI bookkeeper specifically designed for Indian GST compliance and small business needs.',
                globalSource: 'YC',
                globalReference: 'Pilot (S19)',
                successScore: 92,
                status: 'Validating',
                indianCompetitors: 'Zoho Books, Tally (legacy), Khatabook (basic)',
                gapAnalysis: 'Existing solutions are either too complex or too basic. Gap for AI-powered, affordable SMB solution.',
                culturalFit: 95,
                logisticsComplexity: 20,
                paymentReadiness: 85,
                timingAlignment: 95,
                monopolyPotential: 65,
                regulatoryRisk: 30,
                executionFeasibility: 90
            }
        }),
        prisma.opportunity.create({
            data: {
                title: 'Creator Economy Monetization Platform',
                description: 'All-in-one platform for Indian creators to monetize content, sell courses, and manage subscriptions.',
                globalSource: 'Product Hunt',
                globalReference: 'Gumroad, Patreon alternatives',
                successScore: 78,
                status: 'New',
                indianCompetitors: 'Graphy (courses), Instamojo (basic payments)',
                gapAnalysis: 'No unified platform for Indian creators. UPI integration and local payment methods are key differentiators.',
                culturalFit: 88,
                logisticsComplexity: 30,
                paymentReadiness: 90,
                timingAlignment: 85,
                monopolyPotential: 55,
                regulatoryRisk: 25,
                executionFeasibility: 75
            }
        }),
        prisma.opportunity.create({
            data: {
                title: 'AI Recruitment Platform for Blue-Collar Jobs',
                description: 'Automated hiring platform for factory workers, delivery personnel, and service jobs.',
                globalSource: 'YC',
                globalReference: 'Fountain (hiring platform)',
                successScore: 88,
                status: 'New',
                indianCompetitors: 'Apna (partial), WorkIndia (basic listings)',
                gapAnalysis: 'Existing platforms lack AI matching. Massive underserved market of 400M+ workers.',
                culturalFit: 92,
                logisticsComplexity: 35,
                paymentReadiness: 70,
                timingAlignment: 90,
                monopolyPotential: 75,
                regulatoryRisk: 20,
                executionFeasibility: 82
            }
        }),
        prisma.opportunity.create({
            data: {
                title: 'Telemedicine for Tier-2/3 Cities',
                description: 'Affordable video consultations with AI-assisted diagnostics for underserved regions.',
                globalSource: 'YC',
                globalReference: 'Ro Health, Hims',
                successScore: 81,
                status: 'Building',
                indianCompetitors: 'Practo (urban focus), 1mg (pharmacy-first)',
                gapAnalysis: 'Urban-focused competitors ignore 70% of India. Huge opportunity in vernacular, affordable healthcare.',
                culturalFit: 85,
                logisticsComplexity: 45,
                paymentReadiness: 65,
                timingAlignment: 88,
                monopolyPotential: 60,
                regulatoryRisk: 55,
                executionFeasibility: 70
            }
        }),
        prisma.opportunity.create({
            data: {
                title: 'B2B Procurement Marketplace for Kirana Stores',
                description: 'Digital wholesale platform connecting FMCG brands directly with small retailers.',
                globalSource: 'YC',
                globalReference: 'Faire (wholesale marketplace)',
                successScore: 76,
                status: 'New',
                indianCompetitors: 'Udaan (large but struggling), JioMart B2B',
                gapAnalysis: 'Udaan has unit economics issues. Opportunity for focused, profitable model.',
                culturalFit: 90,
                logisticsComplexity: 60,
                paymentReadiness: 75,
                timingAlignment: 70,
                monopolyPotential: 50,
                regulatoryRisk: 30,
                executionFeasibility: 65
            }
        }),
        prisma.opportunity.create({
            data: {
                title: 'AI Tutor for Competitive Exam Prep',
                description: 'Personalized AI tutoring for JEE, NEET, UPSC with adaptive learning paths.',
                globalSource: 'Product Hunt',
                globalReference: 'Khanmigo, Synthesis AI',
                successScore: 89,
                status: 'Validating',
                indianCompetitors: 'Unacademy (video-based), BYJU\'s (struggling)',
                gapAnalysis: 'Existing players are video-heavy. True AI personalization is missing. Post-BYJU\'s market disruption.',
                culturalFit: 95,
                logisticsComplexity: 20,
                paymentReadiness: 88,
                timingAlignment: 95,
                monopolyPotential: 60,
                regulatoryRisk: 15,
                executionFeasibility: 85
            }
        }),
        prisma.opportunity.create({
            data: {
                title: 'Electric Vehicle Fleet Management',
                description: 'SaaS platform for managing commercial EV fleets with charging optimization.',
                globalSource: 'YC',
                globalReference: 'Samsara, Fleet EV solutions',
                successScore: 72,
                status: 'New',
                indianCompetitors: 'Euler Motors (manufacturer), no pure SaaS player',
                gapAnalysis: 'India EV adoption accelerating. No dedicated fleet management software for Indian market.',
                culturalFit: 70,
                logisticsComplexity: 50,
                paymentReadiness: 60,
                timingAlignment: 75,
                monopolyPotential: 65,
                regulatoryRisk: 35,
                executionFeasibility: 68
            }
        })
    ])

    console.log(`✅ Created ${opportunities.length} opportunities`)

    console.log('🎉 Database seeded successfully!')
}

main()
    .catch((e) => {
        console.error('❌ Error seeding database:', e)
        process.exit(1)
    })
    .finally(async () => {
        await prisma.$disconnect()
    })
