/**
 * About page with information about the site and disclaimer
 */
import { Box, Typography, Paper, Divider } from '@mui/material';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

function About() {
  useDocumentTitle('About - FDA Drug Approval Tracker');

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        About FDA Drug Approval Tracker
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Mission
        </Typography>
        <Typography variant="body1" paragraph>
          FDA Drug Approval Tracker provides a comprehensive, searchable database of FDA drug
          approvals and upcoming regulatory events. Our goal is to make FDA approval information
          more accessible to investors, healthcare professionals, patients, and researchers.
        </Typography>

        <Divider sx={{ my: 3 }} />

        <Typography variant="h6" gutterBottom>
          Data Sources
        </Typography>
        <Typography variant="body1" paragraph>
          All data on this site is sourced from publicly available FDA resources, including:
        </Typography>
        <Typography component="ul" variant="body1">
          <li>FDA Center for Drug Evaluation and Research (CDER)</li>
          <li>FDA Center for Biologics Evaluation and Research (CBER)</li>
          <li>FDA Drugs@FDA database</li>
          <li>FDA press releases and announcements</li>
          <li>Public PDUFA date calendars</li>
        </Typography>

        <Divider sx={{ my: 3 }} />

        <Typography variant="h6" gutterBottom>
          Features
        </Typography>
        <Typography component="ul" variant="body1">
          <li>Search and filter FDA drug approvals by therapeutic area, sponsor, and date</li>
          <li>Track upcoming PDUFA dates and advisory committee meetings</li>
          <li>View detailed drug information including approval history</li>
          <li>Browse summary statistics and trends in FDA approvals</li>
          <li>Filter by FDA center (CDER vs CBER) and application type (NDA, BLA, etc.)</li>
        </Typography>

        <Divider sx={{ my: 3 }} />

        <Typography variant="h6" gutterBottom color="error">
          Important Disclaimers
        </Typography>
        <Typography variant="body1" paragraph>
          <strong>Not Medical Advice:</strong> This website is for informational purposes only and
          does not constitute medical advice. Always consult with a qualified healthcare
          professional for medical decisions.
        </Typography>
        <Typography variant="body1" paragraph>
          <strong>Not Investment Advice:</strong> Information on this site should not be considered
          investment advice. Always conduct your own research and consult with a financial advisor
          before making investment decisions.
        </Typography>
        <Typography variant="body1" paragraph>
          <strong>Data Accuracy:</strong> While we strive to provide accurate and up-to-date
          information, we cannot guarantee the completeness or accuracy of all data. Always verify
          critical information with official FDA sources.
        </Typography>
        <Typography variant="body1" paragraph>
          <strong>Not Affiliated with FDA:</strong> This website is an independent project and is
          not affiliated with, endorsed by, or sponsored by the U.S. Food and Drug Administration
          (FDA).
        </Typography>

        <Divider sx={{ my: 3 }} />

        <Typography variant="h6" gutterBottom>
          Contact & Feedback
        </Typography>
        <Typography variant="body1" paragraph>
          We welcome your feedback and suggestions for improving this resource. For questions,
          corrections, or feature requests, please reach out through our contact form.
        </Typography>

        <Divider sx={{ my: 3 }} />

        <Typography variant="h6" gutterBottom>
          Privacy & Cookies
        </Typography>
        <Typography variant="body1" paragraph>
          This site may use cookies for analytics and advertising purposes. We do not collect
          personally identifiable information without your consent. See our Privacy Policy for
          more details.
        </Typography>

        <Divider sx={{ my: 3 }} />

        <Typography variant="body2" color="text.secondary" align="center">
          Version 1.0.0 | © {new Date().getFullYear()} FDA Drug Approval Tracker
        </Typography>
      </Paper>
    </Box>
  );
}

export default About;
