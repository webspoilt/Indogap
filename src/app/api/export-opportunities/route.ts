import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const format = searchParams.get('format') || 'csv' // 'csv' or 'json'

    // Fetch all opportunities
    const opportunities = await db.opportunity.findMany({
      include: {
        globalStartup: true,
        roadmaps: true
      },
      orderBy: { createdAt: 'desc' }
    })

    if (format === 'json') {
      // Return as JSON
      return new NextResponse(JSON.stringify(opportunities, null, 2), {
        headers: {
          'Content-Type': 'application/json',
          'Content-Disposition': `attachment; filename="opportunities-${Date.now()}.json"`
        }
      })
    }

    // Convert to CSV
    const csvHeader = [
      'ID',
      'Title',
      'Description',
      'Global Source',
      'Global Reference',
      'Success Score',
      'Status',
      'Cultural Fit',
      'Logistics Complexity',
      'Payment Readiness',
      'Timing Alignment',
      'Monopoly Potential',
      'Regulatory Risk',
      'Execution Feasibility',
      'Indian Competitors',
      'Gap Analysis',
      'Notes',
      'Created At'
    ]

    const csvRows = opportunities.map(opp => [
      opp.id,
      `"${opp.title.replace(/"/g, '""')}"`,
      `"${opp.description.replace(/"/g, '""')}"`,
      opp.globalSource,
      `"${opp.globalReference.replace(/"/g, '""')}"`,
      opp.successScore,
      opp.status,
      opp.culturalFit || '',
      opp.logisticsComplexity || '',
      opp.paymentReadiness || '',
      opp.timingAlignment || '',
      opp.monopolyPotential || '',
      opp.regulatoryRisk || '',
      opp.executionFeasibility || '',
      `"${(opp.indianCompetitors || '').replace(/"/g, '""')}"`,
      `"${(opp.gapAnalysis || '').replace(/"/g, '""')}"`,
      `"${(opp.notes || '').replace(/"/g, '""')}"`,
      opp.createdAt
    ])

    const csvContent = [
      csvHeader.join(','),
      ...csvRows.map(row => row.join(','))
    ].join('\n')

    return new NextResponse(csvContent, {
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename="opportunities-${Date.now()}.csv"`
      }
    })
  } catch (error) {
    console.error('Error exporting opportunities:', error)
    return NextResponse.json(
      { error: 'Failed to export opportunities' },
      { status: 500 }
    )
  }
}
