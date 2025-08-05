// console.log('timeseries_coa start');

function isValidCharacter(char) {
    const charCode = char.charCodeAt(0);
    return charCode >= 0 && charCode <= 255; // Valid ASCII range
}

function sanitizeInput(word) {
    let sanitizedString = '';
    for (let i = 0; i < word.length; i++) {
        if (isValidCharacter(word[i])) {
            sanitizedString += word[i]; // Keep valid characters
        } else if (word[i].charCodeAt(0) == 8722) {
            sanitizedString += "-"
        } else {
            // Invalid characters are skipped (not added to sanitizedString)
            console.error('Invalid char: ' + word[i] + ' = ' + word[i].charCodeAt(0));
        };
    }
    return sanitizedString;
}

function safeBtoa(word) {
  try {
    const sanitizedInput = sanitizeInput(word);
    return btoa(sanitizedInput); // Now it's safe to use btoa
  } catch (error) {
    console.error('Failed to sanitize  object:', error);
    throw error;
  }
}

function insertSVGAsObject(svgElement, targetContainer) {
  try {
    // Serialize the SVG to a string
    const svgData = new XMLSerializer().serializeToString(svgElement);
    
    // Ensure proper SVG data URL encoding (no need for base64 if using raw SVG)
    // b64 = btoa(unescape(encodeURIComponent(svgData)));
    b64 = safeBtoa(svgData);
    const svgDataUrl = 'data:image/svg+xml;base64,' + b64;
    
    // Create an object element with the data URL
    const objectElement = document.createElement('object');
    objectElement.setAttribute('type', 'image/svg+xml');
    objectElement.setAttribute('data', svgDataUrl);

    // Append object to the target container
    targetContainer.innerHTML = '';  // Clear existing content
    targetContainer.appendChild(objectElement);
    
    return objectElement;

  } catch (error) {
    console.error('Failed to insert SVG as object:', error);
    throw error;
  }
}

function get_time_series_config(element) {

      let columns = element.getAttribute('data-columns');
      let graph_interpolation = element.getAttribute('data-graph_interpolation');
      let graph_title = element.getAttribute('data-graph_title');
      let graph_xaxis = element.getAttribute('data-graph_xaxis');
      let graph_yaxis = element.getAttribute('data-graph_yaxis');
      let results = element.getAttribute('data-results');
      
      try {
        columns = JSON.parse(columns);
        results = JSON.parse(results);
      } catch (e) {
        console.error("JSON parsing error:", e);
      }
      
      // Prep results
      new_results = []
      for (let i = 0; i < results.length; i++) {
        row = results[i];
        new_row = []
        for (let j = 0; j < row.length; j++) {
          item = row[j];
          val = item['val'];
          if (val.length > 0) {
            new_row.push(val);
          }
        };
        new_results.push(new_row);
      }
      
      // Create config for TimeSeries
      return {
        container: element,  // Pass the DOM element directly
        state: { value: new_results },
        props: {
          item: {
            time_series_columns: columns,
            time_series_graph_interpolation: graph_interpolation,
            time_series_graph_title: graph_title,
            time_series_graph_xaxis: graph_xaxis,
            time_series_graph_yaxis: graph_yaxis,
          }
        }
      }; 
}

function renderChart(el) {
  const config = get_time_series_config(el);
  const ts = new TimeSeries(config);

  try {
    const container = d3.select(el);
    container.selectAll("svg").remove();  // Clear existing SVGs
    container.selectAll("img").remove();  // Clear existing SVGs

    ts.build_graph(config);

    const svg = container.selectAll("svg")
    insertSVGAsObject(svg.node(), container.node())
    console.log('insertSVGAsObject');

  } catch (e) {
    console.error("Graph build failed:", e);
  }
};

// console.log('timeseries_coa loaded');
