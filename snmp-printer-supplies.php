<?php
function check_printer_supplies( $ipaddress, $supplycount=null ) {
    $printer_model = 'HOST-RESOURCES-MIB::hrDeviceDescr.1';
    $name_base     = 'SNMPv2-SMI::mib-2.43.11.1.1.6.1.';
    $value_base    = 'SNMPv2-SMI::mib-2.43.11.1.1.9.1.';
    $total_base    = 'SNMPv2-SMI::mib-2.43.11.1.1.8.1.';

    $model_command = 'snmpwalk -v 1 -c public -O va ' . $ipaddress . ' ' . $printer_model;
    $model_output = shell_exec( $model_command );
    $model_output = str_replace( 'STRING: ', '', $model_output );

    $html  = "<h1>$model_output <small>$ipaddress</small></h1>";
    $html .= '<table border=1>';
    $html .= '<thead><tr><th style="width:30vw;">Supply</th><th>Remaining</th><th>Order?</th></tr></thead>';
    $html .= '<tbody>';

    $i=1;
    $supplycount = ( is_null( $supplycount )  ) ? get_number_of_supply_types( $ipaddress ) : $supplycount; // reduce lookups by specifying manually.
    
    while ( $i<=$supplycount ) {
        
        $name_output  = exec_snmpwalk( $ipaddress, $name_base . $i );
        $value_output = exec_snmpwalk( $ipaddress, $value_base . $i );
        $total_output = exec_snmpwalk( $ipaddress, $total_base . $i );

        $need_to_order = ( $value_output > 0 && $value_output < 20 ) ? "Yes" : "";
        
        $style_ip_code       = substr( $ipaddress, -3 );
	    $style_supply_colour = get_colour_from_name_output( $name_output );
		
		if ( $value_output > 0 ) {
	        $percent = floor( $value_output / $total_output * 100 );
	        $value   = $percent . '%';
	        $style_css .= ".$style_supply_colour-$style_ip_code:before{width:$value;}";
		} else {
	        $value = $value_output . '/ ' . $total_output; // because Toner Collection Unit returns negative values (not sure what they mean yet).
		}
	 
        $html .= '<tr>';
        $html .= "<td>$name_output</td>";
        $html .= "<td><div class='percent $style_supply_colour $style_supply_colour-$style_ip_code'><p>$value</p></div></td>";
        $html .= "<td>$need_to_order</td>";
        $html .= '</tr>';
        
        $i++;
    }

    $html .= "</tbody></table>"; 

    return array( 'style' => $style_css, 'html' => $html );
}

function exec_snmpwalk( $ipaddress, $lookup, $options='va' ) {
    $cmd     = 'snmpwalk -v 1 -c public -O' . ' ' . $options . ' ' . $ipaddress . ' ' . $lookup;
    $result  = shell_exec( $cmd );
    $result  = str_replace( 'STRING: ', '', $result );
    $result  = str_replace( 'INTEGER: ', '', $result );
    $result  = str_replace( '"', '', $result );
    $result  = trim( $result );
    
    return $result;	
}

function get_colour_from_name_output( $string ) {
    $string = explode( ' ', $string );
    $string = strtolower( $string[0] );
    $string = trim( $string );
    return $string;
}

function get_number_of_supply_types( $ipaddress ) {
	$supplies_base = 'SNMPv2-SMI::mib-2.43.11.1.1.6.1';
	$string        = exec_snmpwalk( $ipaddress, $supplies_base, 'a' );
	$count         = substr_count( $string, '=' );
	return $count;
}

$printer1 = check_printer_supplies( '192.168.0.101' );
$printer2 = check_printer_supplies( '192.168.0.102', 5 ); // 6 = toner collection
$printer3 = check_printer_supplies( '192.168.0.103', 6 ); // 7 = toner collection
$printer4 = check_printer_supplies( '192.168.0.104', 4 );
$printer5 = check_printer_supplies( '192.168.0.105', 9 );
$printer6 = check_printer_supplies( '192.168.0.107', 1 );


?>
<html>
	<head>
	<title>Printers</title>
		<style>
		.percent {
		    width:200px;
		    height:50px;
		    border:1px solid black;
		    position:relative;
		}
		.percent p {
		    position:absolute;
		    right:5;
		}
		.percent:before {
			background: #eee;
		    content:'\A';
		    position:absolute;
		    top:0; bottom:0;
		    left:0;
		}
		.cyan:before { background-color: #0ff; }
		.magenta:before { background-color: #f0f; }
		.yellow:before { background-color: #ff0; }
		.black:before { background-color: #bbb; }
		<?php 
		    echo $printer1['style'];
		    echo $printer2['style'];
		    echo $printer3['style'];
		    echo $printer4['style'];
		    echo $printer5['style'];
		    echo $printer6['style'];
		?>
		</style>
	</head> 
	<body> 
	<?php 
	    echo $printer1['html'];
	    echo $printer2['html'];
	    echo $printer3['html'];
	    echo $printer4['html'];
	    echo $printer5['html'];
	    echo $printer6['html'];
	?>  
	</body>
</html>
