import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const opportunity = await db.opportunity.findUnique({
      where: { id: params.id },
      include: {
        globalStartup: true,
        roadmaps: true
      }
    })

    if (!opportunity) {
      return NextResponse.json(
        { error: 'Opportunity not found' },
        { status: 404 }
      )
    }

    return NextResponse.json(opportunity)
  } catch (error) {
    console.error('Error fetching opportunity:', error)
    return NextResponse.json(
      { error: 'Failed to fetch opportunity' },
      { status: 500 }
    )
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json()

    const opportunity = await db.opportunity.update({
      where: { id: params.id },
      data: {
        title: body.title,
        globalStartupId: body.globalStartupId,
        description: body.description,
        globalSource: body.globalSource,
        globalReference: body.globalReference,
        successScore: body.successScore,
        status: body.status,
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
      },
      include: {
        globalStartup: true,
        roadmaps: true
      }
    })

    return NextResponse.json(opportunity)
  } catch (error) {
    console.error('Error updating opportunity:', error)
    return NextResponse.json(
      { error: 'Failed to update opportunity' },
      { status: 500 }
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    await db.opportunity.delete({
      where: { id: params.id }
    })

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error deleting opportunity:', error)
    return NextResponse.json(
      { error: 'Failed to delete opportunity' },
      { status: 500 }
    )
  }
}
