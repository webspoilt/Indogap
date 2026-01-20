import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const search = searchParams.get('search')
    const category = searchParams.get('category')

    const where: any = {}

    if (search) {
      where.OR = [
        { name: { contains: search, mode: 'insensitive' } },
        { description: { contains: search, mode: 'insensitive' } }
      ]
    }

    if (category && category !== 'all') {
      where.category = category
    }

    const startups = await db.indianStartup.findMany({
      where,
      orderBy: { createdAt: 'desc' }
    })

    return NextResponse.json(startups)
  } catch (error) {
    console.error('Error fetching Indian startups:', error)
    return NextResponse.json(
      { error: 'Failed to fetch Indian startups' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const startup = await db.indianStartup.create({
      data: {
        name: body.name,
        description: body.description,
        category: body.category,
        foundedDate: body.foundedDate,
        stage: body.stage,
        funding: body.funding,
        source: body.source,
        website: body.website,
        tags: body.tags
      }
    })

    return NextResponse.json(startup, { status: 201 })
  } catch (error) {
    console.error('Error creating Indian startup:', error)
    return NextResponse.json(
      { error: 'Failed to create Indian startup' },
      { status: 500 }
    )
  }
}
