import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { globalStartupName, globalStartupDescription, globalStartupCategory } = body

    if (!globalStartupName || !globalStartupDescription) {
      return NextResponse.json(
        { error: 'Startup name and description are required' },
        { status: 400 }
      )
    }

    // Fetch all Indian startups from the knowledge graph
    const indianStartups = await db.indianStartup.findMany()

    // In production, this would use vector embeddings and similarity search
    // For now, we'll use keyword-based matching as a simplified approach

    const similarities = indianStartups.map(startup => {
      const similarityScore = calculateSimilarity(
        globalStartupDescription.toLowerCase(),
        startup.description.toLowerCase(),
        globalStartupCategory?.toLowerCase(),
        startup.category.toLowerCase()
      )

      return {
        startup,
        similarityScore
      }
    })

    // Sort by similarity score (descending)
    similarities.sort((a, b) => b.similarityScore - a.similarityScore)

    // Find the highest similarity score
    const highestSimilarity = similarities.length > 0 ? similarities[0].similarityScore : 0

    // Determine if there's a gap
    const isGap = highestSimilarity < 60 // Threshold for gap detection

    // Generate gap analysis
    const gapAnalysis = {
      isGap,
      confidenceScore: Math.round(100 - highestSimilarity),
      similarStartups: similarities.filter(s => s.similarityScore > 30).slice(0, 5),
      recommendation: generateRecommendation(isGap, highestSimilarity, similarities)
    }

    return NextResponse.json({
      success: true,
      gapAnalysis
    })
  } catch (error) {
    console.error('Error detecting gaps:', error)
    return NextResponse.json(
      { error: 'Failed to detect gaps' },
      { status: 500 }
    )
  }
}

// Simple similarity calculation based on keyword overlap
// In production, this would use proper vector embeddings (e.g., OpenAI text-embedding-3-small)
function calculateSimilarity(
  globalDesc: string,
  indianDesc: string,
  globalCategory?: string,
  indianCategory?: string
): number {
  const globalWords = extractKeywords(globalDesc)
  const indianWords = extractKeywords(indianDesc)

  // Calculate keyword overlap
  let overlap = 0
  globalWords.forEach(word => {
    if (indianWords.includes(word)) {
      overlap++
    }
  })

  // Base similarity from keyword overlap
  let similarity = 0
  if (globalWords.length > 0) {
    similarity = (overlap / globalWords.length) * 100
  }

  // Boost similarity if categories match
  if (globalCategory && indianCategory && globalCategory === indianCategory) {
    similarity += 30
  }

  // Cap at 100
  return Math.min(100, Math.round(similarity))
}

// Extract keywords from text (simplified)
function extractKeywords(text: string): string[] {
  // Remove common stop words and punctuation
  const stopWords = new Set([
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'should', 'could', 'may', 'might', 'must', 'shall', 'can', 'need',
    'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
    'we', 'they', 'what', 'which', 'who', 'whom', 'when', 'where', 'why',
    'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
    'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there', 'then',
    'once', 'about', 'into', 'through', 'during', 'before', 'after', 'above',
    'below', 'between', 'under', 'again', 'further', 'their', 'your', 'our',
    'its', 'my', 'his', 'her', 'their', 'as', 'if'
  ])

  const words = text
    .toLowerCase()
    .replace(/[^\w\s]/g, '')
    .split(/\s+/)
    .filter(word => word.length > 2 && !stopWords.has(word))

  return [...new Set(words)] // Return unique words
}

function generateRecommendation(
  isGap: boolean,
  highestSimilarity: number,
  similarities: any[]
): string {
  if (isGap) {
    return `This represents a strong opportunity gap in the Indian market. With ${Math.round(100 - highestSimilarity)}% confidence, there's no direct equivalent in the current Indian startup landscape. The high gap score suggests this concept has potential for first-mover advantage. Consider building an MVP to validate market interest.`
  } else if (highestSimilarity > 80) {
    const similarStartup = similarities[0]?.startup?.name || 'existing players'
    return `This market appears to be saturated. There are strong similarities with ${similarStartup} (${highestSimilarity}% match). Proceed with caution as competition is likely intense. Consider either targeting a different niche or finding a significant differentiation point.`
  } else {
    return `Moderate opportunity exists. While similar concepts exist in India (${Math.round(100 - highestSimilarity)}% gap confidence), there may be room for improvement or differentiation. Focus on understanding why existing solutions haven't fully captured the market and address those gaps.`
  }
}
