import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const search = searchParams.get('search')
    const source = searchParams.get('source')
    const status = searchParams.get('status')
    const minScore = searchParams.get('minScore')

    const where: any = {}

    if (search) {
      where.OR = [
        { title: { contains: search, mode: 'insensitive' } },
        { description: { contains: search, mode: 'insensitive' } }
      ]
    }

    if (source && source !== 'all') {
      where.globalSource = source
    }

    if (status && status !== 'all') {
      where.status = status
    }

    if (minScore) {
      where.successScore = { gte: parseInt(minScore) }
    }

    const opportunities = await db.opportunity.findMany({
      where,
      include: {
        globalStartup: true,
        roadmaps: true
      },
      orderBy: { createdAt: 'desc' }
    })

    return NextResponse.json(opportunities)
  } catch (error) {
    console.error('Error fetching opportunities:', error)
    return NextResponse.json(
      { error: 'Failed to fetch opportunities' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const opportunity = await db.opportunity.create({
      data: {
        title: body.title,
        globalStartupId: body.globalStartupId,
        description: body.description,
        globalSource: body.globalSource,
        globalReference: body.globalReference,
        successScore: body.successScore,
        status: body.status || 'New',
        indianCompetitors: body.indianCompetitors,
        gapAnalysis: body.gapAnalysis,
        culturalFit: body.culturalFit,
        logisticsComplexity: body.logisticsComplexity,
        paymentReadiness: body.paymentReadiness,
        timingAlignment: body.timingAlignment,
        monopolyPotential: body.monopolyPotential,
        regulatoryRisk: body.regulatoryRisk,
        executionFeasibility: body.executionFeasibility,
        notes: body.notes
      }
    })

    return NextResponse.json(opportunity, { status: 201 })
  } catch (error) {
    console.error('Error creating opportunity:', error)
    return NextResponse.json(
      { error: 'Failed to create opportunity' },
      { status: 500 }
    )
  }
}
