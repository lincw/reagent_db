class BlastService
  def process_results(xml_results)
    hits = []
    xml_results.search("//Hit").each do |hit|
      hit_def = hit.search("Hit_def").text
      hit_accession = hit.search("Hit_accession").text
      hit_len = hit.search("Hit_len").text.to_i
      
      # Extract ID from hit_def (assuming format like "lcl|123 description")
      seq_id = hit_def.split('|')[1]&.split(' ')&.first || hit_accession
      
      # Find the sequence in the database
      sequence = Sequence.find_by(id: seq_id)
      
      # Initialize gene information
      gene_symbol = nil
      original_name = hit_def
      
      if sequence
        # Try to get gene symbol through different approaches
        gene_symbol = find_gene_symbol(sequence, hit_def)
        
        # Get original name if available
        if sequence.respond_to?(:name) && sequence.name.present?
          original_name = sequence.name
        elsif sequence.respond_to?(:human_gene) && sequence.human_gene&.original_name.present?
          original_name = sequence.human_gene.original_name
        end
      end
      
      # Get the first HSP (High-scoring Segment Pair)
      hsp = hit.search("Hit_hsps/Hsp").first
      
      if hsp
        hsp_bit_score = hsp.search("Hsp_bit-score").text.to_f
        hsp_score = hsp.search("Hsp_score").text.to_i
        hsp_evalue = hsp.search("Hsp_evalue").text.to_f
        hsp_query_from = hsp.search("Hsp_query-from").text.to_i
        hsp_query_to = hsp.search("Hsp_query-to").text.to_i
        hsp_hit_from = hsp.search("Hsp_hit-from").text.to_i
        hsp_hit_to = hsp.search("Hsp_hit-to").text.to_i
        hsp_identity = hsp.search("Hsp_identity").text.to_i
        hsp_positive = hsp.search("Hsp_positive").text.to_i
        hsp_gaps = hsp.search("Hsp_gaps").text.to_i
        hsp_align_len = hsp.search("Hsp_align-len").text.to_i
        
        hits << {
          hit_num: hits.count + 1,
          hit_id: seq_id,
          hit_def: hit_def,
          gene_symbol: gene_symbol || '-',
          original_name: original_name,
          hit_len: hit_len,
          hsp_bit_score: hsp_bit_score,
          hsp_score: hsp_score,
          hsp_evalue: hsp_evalue,
          hsp_query_from: hsp_query_from,
          hsp_query_to: hsp_query_to,
          hsp_hit_from: hsp_hit_from,
          hsp_hit_to: hsp_hit_to,
          hsp_identity: hsp_identity,
          hsp_positive: hsp_positive,
          hsp_gaps: hsp_gaps,
          hsp_align_len: hsp_align_len
        }
      end
    end
    hits
  end
  
  private
  
  def find_gene_symbol(sequence, hit_def)
    # Check direct attributes first (no Rails dependencies)
    if has_attribute?(sequence, :human_gene) && sequence.human_gene
      return sequence.human_gene.hgnc_symbol if has_attribute?(sequence.human_gene, :hgnc_symbol) && sequence.human_gene.hgnc_symbol
    end
    
    # Check gene_name attribute
    if has_attribute?(sequence, :gene_name) && !empty?(sequence.gene_name)
      return sequence.gene_name
    end
    
    # Try to find gene symbol by name or id
    name_to_try = nil
    
    # Try sequence name if available
    if has_attribute?(sequence, :name) && !empty?(sequence.name)
      name_to_try = sequence.name
    end
    
    # Then try extracting from hit_def
    if empty?(name_to_try) || name_to_try == hit_def
      name_to_try = extract_gene_name_from_hit_def(hit_def)
    end
    
    # Try sequence ID if it looks like a gene name
    if empty?(name_to_try) && sequence.id.to_s =~ /^[A-Z0-9]+$/i
      name_to_try = sequence.id.to_s
    end
    
    # Try database lookup if we can access database
    if !empty?(name_to_try) && defined?(HumanGene)
      human_gene = simple_find_human_gene(name_to_try)
      if human_gene && has_attribute?(human_gene, :hgnc_symbol) && !empty?(human_gene.hgnc_symbol)
        return human_gene.hgnc_symbol
      end
    end
    
    nil
  end
  
  # Helper methods that avoid Rails dependencies
  
  def has_attribute?(obj, attr)
    obj.respond_to?(attr)
  end
  
  def empty?(value)
    value.nil? || (value.respond_to?(:empty?) && value.empty?)
  end
  
  # Simplified human gene lookup without Rails-specific queries
  def simple_find_human_gene(name)
    return nil if empty?(name)
    
    # Try to find by name however your data access layer allows
    # This is a simplified placeholder - implement based on your data access method
    if defined?(HumanGene) && HumanGene.respond_to?(:find_by_name)
      HumanGene.find_by_name(name)
    elsif defined?(HumanGene) && HumanGene.respond_to?(:where)
      # Minimal query if ActiveRecord-like interface is available
      HumanGene.where(original_name: name).first
    else
      nil
    end
  end
  
  def extract_gene_name_from_hit_def(hit_def)
    # Attempt to extract gene names like MGC2752 from hit_def
    gene_patterns = [
      /\b(MGC\d+)\b/i,                    # Match MGC followed by numbers
      /\b([A-Z0-9]{2,})\s+protein\b/i,    # Match gene name followed by "protein"
      /protein\s+([A-Z0-9]{2,})\b/i,      # Match "protein" followed by gene name
      /\b([A-Z]{2,}[0-9]{1,})\b/i         # Match letters followed by numbers
    ]
    
    gene_patterns.each do |pattern|
      match = hit_def.match(pattern)
      return match[1] if match
    end
    
    nil
  end
end