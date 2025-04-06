namespace :blast_debug do
  desc "Test gene symbol mapping for MGC2752"
  task test_mgc2752: :environment do
    puts "Testing gene symbol mapping for MGC2752"
    
    # Create a test sequence with MGC2752
    test_sequence = Sequence.new(id: 999999, name: "MGC2752 test sequence")
    hit_def = "lcl|123 MGC2752 protein homolog"
    
    service = BlastService.new
    gene_symbol = service.send(:find_gene_symbol, test_sequence, hit_def)
    
    puts "Input:"
    puts "- Sequence ID: #{test_sequence.id}"
    puts "- Sequence name: #{test_sequence.name}"
    puts "- Hit definition: #{hit_def}"
    puts "Result:"
    puts "- Gene symbol: #{gene_symbol || 'nil'}"
    
    if gene_symbol == "CENPBD2P"
      puts "SUCCESS: MGC2752 correctly mapped to CENPBD2P!"
    else
      puts "FAILURE: MGC2752 was not mapped to CENPBD2P"
    end
    
    # Check the actual database for MGC2752
    if ActiveRecord::Base.connection.table_exists?('human_genes')
      puts "\nChecking database for MGC2752 references:"
      
      # Try different search patterns
      patterns = [
        "%MGC2752%",
        "%mgc2752%",
        "%CENPBD2P%",
        "%cenpbd2p%"
      ]
      
      patterns.each do |pattern|
        genes = HumanGene.where("original_name LIKE ?", pattern)
        puts "- Search '#{pattern}': Found #{genes.count} genes"
        genes.each do |gene|
          puts "  * ID: #{gene.id}, HGNC: #{gene.hgnc_symbol}, Original: #{gene.original_name}"
        end
      end
      
      # If HumanGene has an aliases column, check that too
      if HumanGene.column_names.include?('aliases')
        patterns.each do |pattern|
          genes = HumanGene.where("aliases LIKE ?", pattern)
          puts "- Aliases search '#{pattern}': Found #{genes.count} genes"
          genes.each do |gene|
            puts "  * ID: #{gene.id}, HGNC: #{gene.hgnc_symbol}, Aliases: #{gene.aliases}"
          end
        end
      end
    end
  end
end
