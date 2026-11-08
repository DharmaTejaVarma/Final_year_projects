import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

export const pdfExportService = {
  generateItineraryPdf(itinerary) {
    if (!itinerary) return;

    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'pt',
      format: 'a4',
    });

    const primaryColor = [15, 23, 42]; // Slate 900
    const accentColor = [56, 189, 248]; // Sky 400
    const darkGray = [71, 85, 105];

    // --- Header Banner ---
    doc.setFillColor(...primaryColor);
    doc.rect(0, 0, 595.28, 90, 'F');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(22);
    doc.setTextColor(255, 255, 255);
    doc.text('TravelSenseAI', 40, 42);

    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...accentColor);
    doc.text('Smart AI-Powered Travel Itinerary & Tour Plan', 40, 64);

    doc.setFontSize(9);
    doc.setTextColor(200, 200, 200);
    const dateStr = new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
    doc.text(`Generated: ${dateStr}`, 470, 42);
    doc.text(`ID: ${itinerary.itinerary_id || 'N/A'}`, 470, 58);

    // --- Trip Overview Box ---
    let currentY = 115;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(14);
    doc.setTextColor(...primaryColor);
    doc.text(`Trip Summary: ${itinerary.destination}`, 40, currentY);

    currentY += 15;
    const summaryData = [
      [
        { content: 'Destination:', styles: { fontStyle: 'bold' } },
        itinerary.destination,
        { content: 'Total Duration:', styles: { fontStyle: 'bold' } },
        `${itinerary.total_days} Day(s)`,
      ],
      [
        { content: 'Dates:', styles: { fontStyle: 'bold' } },
        `${itinerary.start_date} to ${itinerary.end_date}`,
        { content: 'Travelers:', styles: { fontStyle: 'bold' } },
        `${itinerary.travelers_count} person(s)`,
      ],
      [
        { content: 'Total Road Distance:', styles: { fontStyle: 'bold' } },
        `${itinerary.total_distance_km} km`,
        { content: 'Total Estimated Cost:', styles: { fontStyle: 'bold' } },
        `INR ${Number(itinerary.budget_summary?.estimated_total_cost || 0).toLocaleString('en-IN', {
          maximumFractionDigits: 2,
        })}`,
      ],
      [
        { content: 'Pace & Transport:', styles: { fontStyle: 'bold' } },
        `${itinerary.pace || 'moderate'} | ${itinerary.transportation || 'driving-car'}`,
        { content: 'Feasibility Status:', styles: { fontStyle: 'bold' } },
        `${(itinerary.feasibility_status || 'feasible').toUpperCase()}`,
      ],
    ];

    autoTable(doc, {
      startY: currentY,
      body: summaryData,
      theme: 'grid',
      styles: { fontSize: 9, cellPadding: 4 },
      headStyles: { fillColor: primaryColor },
      margin: { left: 40, right: 40 },
    });

    currentY = doc.lastAutoTable.finalY + 25;

    // --- Schedule Table ---
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.setTextColor(...primaryColor);
    doc.text('Day-by-Day Visiting Schedule', 40, currentY);

    const scheduleRows = [];
    (itinerary.days || []).forEach((day) => {
      // Day Header row
      scheduleRows.push([
        {
          content: `Day ${day.day_number}: ${day.theme || 'Exploration'} (${day.date})`,
          colSpan: 5,
          styles: {
            fontStyle: 'bold',
            fillColor: [241, 245, 249],
            textColor: primaryColor,
          },
        },
      ]);

      (day.stops || []).forEach((stop) => {
        if (!stop.is_start_location && !stop.is_end_location) {
          scheduleRows.push([
            `Stop #${stop.stop_order}`,
            stop.name,
            `${stop.arrival_time} - ${stop.departure_time}`,
            `${stop.visit_duration_mins} mins`,
            stop.total_entrance_fee > 0
              ? `INR ${Number(stop.total_entrance_fee).toFixed(0)}`
              : 'Free / Included',
          ]);
        }
      });

      (day.meal_breaks || []).forEach((meal) => {
        scheduleRows.push([
          'Meal',
          `Dining: ${meal.name}`,
          `${meal.scheduled_start} - ${meal.scheduled_end}`,
          `${meal.duration_mins} mins`,
          `INR ${Number(meal.estimated_cost || 0).toFixed(0)}`,
        ]);
      });
    });

    autoTable(doc, {
      startY: currentY + 10,
      head: [['Seq', 'Attraction / Stop', 'Scheduled Time', 'Duration', 'Admission']],
      body: scheduleRows,
      theme: 'striped',
      headStyles: { fillColor: primaryColor, fontSize: 9 },
      bodyStyles: { fontSize: 8.5 },
      margin: { left: 40, right: 40 },
    });

    // --- Budget Breakdown Table ---
    if (itinerary.budget_summary?.category_breakdown) {
      currentY = doc.lastAutoTable.finalY + 25;

      // Add a page if low on space
      if (currentY > 680) {
        doc.addPage();
        currentY = 40;
      }

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(13);
      doc.setTextColor(...primaryColor);
      doc.text('Financial Budget Breakdown', 40, currentY);

      const b = itinerary.budget_summary;
      const cb = b.category_breakdown;
      const total = b.estimated_total_cost || 1;

      const budgetRows = [
        ['Road Transportation', `INR ${cb.transportation?.toFixed(2)}`, `${((cb.transportation / total) * 100).toFixed(1)}%`],
        ['Attraction Entrance Fees', `INR ${cb.entrance_fees?.toFixed(2)}`, `${((cb.entrance_fees / total) * 100).toFixed(1)}%`],
        ['Food & Dining', `INR ${cb.food?.toFixed(2)}`, `${((cb.food / total) * 100).toFixed(1)}%`],
        ['Accommodation / Hotel', `INR ${cb.accommodation?.toFixed(2)}`, `${((cb.accommodation / total) * 100).toFixed(1)}%`],
        ['Contingency Buffer (8%)', `INR ${cb.contingency_buffer?.toFixed(2)}`, `${((cb.contingency_buffer / total) * 100).toFixed(1)}%`],
        [
          { content: 'Total Estimated Cost', styles: { fontStyle: 'bold' } },
          { content: `INR ${total.toFixed(2)}`, styles: { fontStyle: 'bold' } },
          { content: '100.0%', styles: { fontStyle: 'bold' } },
        ],
      ];

      autoTable(doc, {
        startY: currentY + 10,
        head: [['Expense Category', 'Estimated Amount', 'Allocation']],
        body: budgetRows,
        theme: 'grid',
        headStyles: { fillColor: primaryColor, fontSize: 9 },
        bodyStyles: { fontSize: 8.5 },
        margin: { left: 40, right: 40 },
      });
    }

    // --- Footer Notice on All Pages ---
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(...darkGray);
      doc.text(
        'TravelSenseAI | Powered by Multi-Criteria Optimization, Geoapify, OpenRouteService & Open-Meteo',
        40,
        820
      );
      doc.text(`Page ${i} of ${pageCount}`, 510, 820);
    }

    const cleanDest = (itinerary.destination || 'Trip').replace(/[^a-zA-Z0-9]/g, '_');
    doc.save(`TravelSenseAI_${cleanDest}_Itinerary.pdf`);
  },
};

export default pdfExportService;

